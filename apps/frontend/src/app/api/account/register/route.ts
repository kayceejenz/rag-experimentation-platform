import { NextResponse } from 'next/server';
import { registerUser } from '@/lib/api/auth';
import { BackendRequestError } from '@/lib/api/backend';

export async function POST(request: Request) {
	try {
		const { email, password, display_name, invitation_code } = (await request.json()) as {
			email: string;
			password: string;
			display_name: string | null;
			invitation_code: string;
		};
		if (!email || !password || !invitation_code) {
			return NextResponse.json(
				{ error: 'Email, password, and invitation code are required.' },
				{ status: 400 },
			);
		}
		const user = await registerUser(
			email.trim().toLowerCase(),
			password,
			display_name?.trim() || null,
			invitation_code,
		);
		return NextResponse.json(user, { status: 201 });
	} catch (error) {
		const message =
			error instanceof Error ? error.message : 'Registration failed.';
		const status = error instanceof BackendRequestError ? error.status : 500;
		return NextResponse.json({ error: message }, { status });
	}
}
