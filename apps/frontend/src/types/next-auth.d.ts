import type { DefaultSession, DefaultJWT } from 'next-auth';

declare module 'next-auth' {
	interface Session {
		accessToken: string;
		error?: 'RefreshAccessTokenError';
		user: {
			id: string;
		} & DefaultSession['user'];
	}
}

declare module 'next-auth/jwt' {
	interface JWT extends DefaultJWT {
		userId: string;
		accessToken: string;
		refreshToken: string;
		accessTokenExpiresAt: number;
		error?: 'RefreshAccessTokenError';
	}
}
