import { NextResponse } from 'next/server';
import { registerUser } from '@/lib/api/auth';

export async function POST(request: Request) {
	try {
		const { email, password, display_name } = (await request.json()) as {
			email: string;
			password: string;
			display_name: string | null;
		};
		if (!email || !password) {
			return NextResponse.json(
				{ error: 'Email and password are required.' },
				{ status: 400 },
			);
		}
		const user = await registerUser(
			email.trim().toLowerCase(),
			password,
			display_name?.trim() || null,
		);
		return NextResponse.json(user, { status: 201 });
	} catch (error) {
		const message =
			error instanceof Error ? error.message : 'Registration failed.';
		return NextResponse.json({ error: message }, { status: 409 });
	}
}
