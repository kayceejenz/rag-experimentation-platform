import { NextResponse } from 'next/server';
import {
	getRefreshToken,
	refreshTokens,
	setAuthCookies,
	getAuthUser,
} from '@/lib/api/auth';

export async function POST() {
	try {
		const refreshToken = await getRefreshToken();
		if (!refreshToken) {
			return NextResponse.json(
				{ error: 'No refresh token.' },
				{ status: 401 },
			);
		}
		const tokens = await refreshTokens(refreshToken);
		if (!tokens) {
			return NextResponse.json(
				{ error: 'Refresh token rejected.' },
				{ status: 401 },
			);
		}
		const user = await getAuthUser();
		if (!user) {
			return NextResponse.json(
				{ error: 'No user session.' },
				{ status: 401 },
			);
		}
		await setAuthCookies(
			tokens.accessToken,
			tokens.refreshToken,
			user.id,
			user.email,
			user.name,
			tokens.expiresIn,
		);
		return NextResponse.json({ ok: true });
	} catch {
		return NextResponse.json(
			{ error: 'Refresh failed.' },
			{ status: 500 },
		);
	}
}
