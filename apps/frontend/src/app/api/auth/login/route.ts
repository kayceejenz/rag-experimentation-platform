import { NextResponse } from 'next/server';
import { loginUser, setAuthCookies } from '@/lib/api/auth';
import { BackendRequestError } from '@/lib/api/backend';

export async function POST(request: Request) {
	try {
		const { email, password } = (await request.json()) as {
			email: string;
			password: string;
		};
		if (!email || !password) {
			return NextResponse.json(
				{ error: 'Email and password are required.' },
				{ status: 400 },
			);
		}
		const { user, refreshToken, expiresIn } = await loginUser(
			email.trim().toLowerCase(),
			password,
		);
		await setAuthCookies(
			user.accessToken,
			refreshToken,
			user.id,
			user.email,
			user.name,
			expiresIn,
		);
		return NextResponse.json({
			user: { id: user.id, email: user.email, name: user.name },
		});
	} catch (error) {
		const message =
			error instanceof Error ? error.message : 'Login failed.';
		const status = error instanceof BackendRequestError ? error.status : 500;
		const headers =
			error instanceof BackendRequestError && error.retryAfter
				? { 'retry-after': error.retryAfter }
				: undefined;
		return NextResponse.json({ error: message }, { status, headers });
	}
}
