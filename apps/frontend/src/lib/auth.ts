import { createHash } from 'node:crypto';
import type { NextAuthOptions, User } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';
import { serverEnv } from '@/lib/env';

type BackendToken = {
	access_token: string;
	token_type: string;
	expires_in: number;
};
type BackendUser = { id: string; email: string; display_name: string | null };
type AuthUser = User & {
	accessToken: string;
	refreshToken: string;
	accessTokenExpiresAt: number;
};

function apiUrl(path: string): string {
	return `${serverEnv.BACKEND_API_URL}/api/v1/auth${path}`;
}

function refreshTokenFrom(response: Response): string | null {
	const cookie = response.headers.get('set-cookie') ?? '';
	return /(?:^|[,;]\s*)refresh_token=([^;,]+)/.exec(cookie)?.[1] ?? null;
}

async function authenticate(
	email: string,
	password: string,
): Promise<AuthUser | null> {
	const login = await fetch(apiUrl('/login'), {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ email, password }),
		cache: 'no-store',
	});
	if (!login.ok) return null;
	const tokens = (await login.json()) as BackendToken;
	const refreshToken = refreshTokenFrom(login);
	if (!refreshToken)
		throw new Error('Backend login did not return a refresh token');

	const profile = await fetch(apiUrl('/me'), {
		headers: { authorization: `Bearer ${tokens.access_token}` },
		cache: 'no-store',
	});
	if (!profile.ok)
		throw new Error('Unable to load the authenticated user');
	const user = (await profile.json()) as BackendUser;
	return {
		id: user.id,
		email: user.email,
		name: user.display_name ?? user.email,
		accessToken: tokens.access_token,
		refreshToken,
		accessTokenExpiresAt: Date.now() + tokens.expires_in * 1000,
	};
}

type RefreshEntry = { promise: Promise<JWT>; expiresAt: number };
const refreshState = globalThis as typeof globalThis & {
	ragappRefreshes?: Map<string, RefreshEntry>;
};
const refreshes =
	refreshState.ragappRefreshes ?? new Map<string, RefreshEntry>();
refreshState.ragappRefreshes = refreshes;

function refreshKey(refreshToken: string) {
	return createHash('sha256').update(refreshToken).digest('hex');
}

async function performRefresh(token: JWT): Promise<JWT> {
	try {
		const response = await fetch(apiUrl('/refresh'), {
			method: 'POST',
			headers: {
				cookie: `refresh_token=${token.refreshToken}`,
			},
			cache: 'no-store',
		});
		if (!response.ok) throw new Error('Refresh token rejected');
		const refreshed = (await response.json()) as BackendToken;
		return {
			...token,
			accessToken: refreshed.access_token,
			refreshToken:
				refreshTokenFrom(response) ??
				token.refreshToken,
			accessTokenExpiresAt:
				Date.now() + refreshed.expires_in * 1000,
			error: undefined,
		};
	} catch {
		return { ...token, error: 'RefreshAccessTokenError' as const };
	}
}

function refreshAccessToken(token: JWT): Promise<JWT> {
	const key = refreshKey(String(token.refreshToken ?? ''));
	const now = Date.now();
	for (const [cachedKey, entry] of refreshes) {
		if (entry.expiresAt <= now) refreshes.delete(cachedKey);
	}
	const existing = refreshes.get(key);
	if (existing) return existing.promise;

	const entry: RefreshEntry = {
		promise: Promise.resolve(token),
		expiresAt: now + 60_000,
	};
	entry.promise = performRefresh(token).then(result => {
		if (result.error) entry.expiresAt = Date.now() + 1_000;
		return result;
	});
	refreshes.set(key, entry);
	return entry.promise;
}

export const authOptions: NextAuthOptions = {
	secret: serverEnv.NEXTAUTH_SECRET,
	session: { strategy: 'jwt', maxAge: 30 * 24 * 60 * 60 },
	providers: [
		CredentialsProvider({
			name: 'Email and password',
			credentials: {
				email: { label: 'Email', type: 'email' },
				password: {
					label: 'Password',
					type: 'password',
				},
			},
			async authorize(credentials) {
				if (
					!credentials?.email ||
					!credentials.password
				)
					return null;
				return authenticate(
					credentials.email.trim().toLowerCase(),
					credentials.password,
				);
			},
		}),
	],
	pages: { signIn: '/auth/signin', error: '/auth/error' },
	callbacks: {
		async redirect({ url, baseUrl }) {
			if (url.startsWith('/')) return `${baseUrl}${url}`;
			const target = new URL(url);
			if (target.origin === baseUrl) return url;
			const isLocalDevelopment =
				process.env.NODE_ENV !== 'production' &&
				(target.hostname === 'localhost' ||
					target.hostname === '127.0.0.1');
			if (isLocalDevelopment) return target.toString();
			return baseUrl;
		},
		async jwt({ token, user }) {
			if (user) {
				const authenticated = user as AuthUser;
				return {
					...token,
					userId: authenticated.id,
					accessToken: authenticated.accessToken,
					refreshToken:
						authenticated.refreshToken,
					accessTokenExpiresAt:
						authenticated.accessTokenExpiresAt,
				};
			}
			if (
				Date.now() <
				Number(token.accessTokenExpiresAt) - 30_000
			)
				return token;
			return refreshAccessToken(token);
		},
		async session({ session, token }) {
			session.user.id = String(token.userId);
			session.accessToken = String(token.accessToken ?? '');
			session.error = token.error;
			return session;
		},
	},
	events: {
		async signOut({ token }) {
			if (!token?.refreshToken) return;
			await fetch(apiUrl('/logout'), {
				method: 'POST',
				headers: {
					cookie: `refresh_token=${token.refreshToken}`,
				},
				cache: 'no-store',
			}).catch(() => undefined);
		},
	},
};
