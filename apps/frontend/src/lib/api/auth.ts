import { cookies } from 'next/headers';
import { serverEnv } from '@/lib/env';
import { BackendRequestError } from '@/lib/api/backend';

const ACCESS_TOKEN = 'access_token';
const REFRESH_TOKEN = 'refresh_token';
const USER_ID = 'user_id';
const USER_EMAIL = 'user_email';
const USER_NAME = 'user_name';

const COOKIE_MAX_AGE = 30 * 24 * 60 * 60;

function cookieOpts(maxAge: number, httpOnly = true) {
	return {
		httpOnly,
		secure: process.env.NODE_ENV === 'production',
		sameSite: 'lax' as const,
		path: '/',
		maxAge,
	};
}

export type AuthUser = {
	id: string;
	email: string;
	name: string;
	accessToken: string;
};

type TokenPayload = {
	access_token: string;
	token_type: string;
	expires_in: number;
};

function apiUrl(path: string): string {
	return `${serverEnv.BACKEND_API_URL}/api/v1/auth${path}`;
}

function extractRefreshToken(response: Response): string | null {
	const header = response.headers.get('set-cookie') ?? '';
	return /(?:^|[,;]\s*)refresh_token=([^;,]+)/.exec(header)?.[1] ?? null;
}

export async function loginUser(
	email: string,
	password: string,
): Promise<{ user: AuthUser; refreshToken: string; expiresIn: number }> {
	const loginRes = await fetch(apiUrl('/login'), {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ email, password }),
		cache: 'no-store',
	});
	if (!loginRes.ok) {
		const body = (await loginRes.json().catch(() => ({}))) as {
			detail?: string;
			error?: { message?: string };
		};
		throw new BackendRequestError(
			body.error?.message ??
				body.detail ??
				'Invalid credentials',
			loginRes.status,
			loginRes.headers.get('retry-after'),
		);
	}
	const tokens = (await loginRes.json()) as TokenPayload;
	const refreshToken = extractRefreshToken(loginRes);
	if (!refreshToken)
		throw new Error('Backend login did not return a refresh token');

	const profileRes = await fetch(apiUrl('/me'), {
		headers: { authorization: `Bearer ${tokens.access_token}` },
		cache: 'no-store',
	});
	if (!profileRes.ok) throw new Error('Unable to load user profile');
	const profile = (await profileRes.json()) as {
		id: string;
		email: string;
		display_name: string | null;
	};

	return {
		user: {
			id: profile.id,
			email: profile.email,
			name: profile.display_name ?? profile.email,
			accessToken: tokens.access_token,
		},
		refreshToken,
		expiresIn: tokens.expires_in,
	};
}

export async function refreshTokens(
	currentRefreshToken: string,
): Promise<{
	accessToken: string;
	refreshToken: string;
	expiresIn: number;
} | null> {
	try {
		const response = await fetch(apiUrl('/refresh'), {
			method: 'POST',
			headers: {
				cookie: `refresh_token=${currentRefreshToken}`,
			},
			cache: 'no-store',
		});
		if (!response.ok) return null;
		const data = (await response.json()) as TokenPayload;
		const newRefreshToken =
			extractRefreshToken(response) ?? currentRefreshToken;
		return {
			accessToken: data.access_token,
			refreshToken: newRefreshToken,
			expiresIn: data.expires_in,
		};
	} catch {
		return null;
	}
}

export async function setAuthCookies(
	accessToken: string,
	refreshToken: string,
	userId: string,
	userEmail: string,
	userName: string,
	expiresIn: number,
): Promise<void> {
	const store = await cookies();
	store.set(ACCESS_TOKEN, accessToken, cookieOpts(expiresIn));
	store.set(REFRESH_TOKEN, refreshToken, cookieOpts(COOKIE_MAX_AGE));
	store.set(USER_ID, userId, cookieOpts(COOKIE_MAX_AGE, false));
	store.set(USER_EMAIL, userEmail, cookieOpts(COOKIE_MAX_AGE, false));
	store.set(USER_NAME, userName, cookieOpts(COOKIE_MAX_AGE, false));
}

export async function logoutUser(): Promise<void> {
	const store = await cookies();
	const refreshToken = store.get(REFRESH_TOKEN)?.value;
	if (refreshToken) {
		await fetch(apiUrl('/logout'), {
			method: 'POST',
			headers: { cookie: `refresh_token=${refreshToken}` },
			cache: 'no-store',
		}).catch(() => undefined);
	}
	store.delete(ACCESS_TOKEN);
	store.delete(REFRESH_TOKEN);
	store.delete(USER_ID);
	store.delete(USER_EMAIL);
	store.delete(USER_NAME);
}

export async function getAuthUser(): Promise<AuthUser | null> {
	const store = await cookies();
	const accessToken = store.get(ACCESS_TOKEN)?.value;
	const userId = store.get(USER_ID)?.value;
	const email = store.get(USER_EMAIL)?.value;
	const name = store.get(USER_NAME)?.value;

	if (!accessToken || !userId) return null;

	return {
		id: userId,
		email: email ?? '',
		name: name ?? '',
		accessToken,
	};
}

export async function registerUser(
	email: string,
	password: string,
	displayName: string | null,
	invitationCode: string,
): Promise<{ id: string; email: string }> {
	const res = await fetch(apiUrl('/register'), {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({
			email,
			password,
			display_name: displayName,
			invitation_code: invitationCode,
		}),
		cache: 'no-store',
	});
	if (!res.ok) {
		const body = (await res.json().catch(() => ({}))) as {
			detail?: string;
			error?: {
				message?: string;
				details?: Array<{ message?: string }>;
			};
		};
		throw new BackendRequestError(
			body.error?.details?.[0]?.message ??
				body.error?.message ??
				body.detail ??
				'Unable to create the account.',
			res.status,
		);
	}
	const data = (await res.json()) as {
		id: string;
		email: string;
		display_name: string | null;
	};
	return { id: data.id, email: data.email };
}

export async function getRefreshToken(): Promise<string | null> {
	const store = await cookies();
	return store.get(REFRESH_TOKEN)?.value ?? null;
}
