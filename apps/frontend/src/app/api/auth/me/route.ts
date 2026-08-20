import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';

export async function GET() {
	const user = await getAuthUser();
	if (!user) {
		return NextResponse.json(
			{ error: 'Not authenticated.' },
			{ status: 401 },
		);
	}
	return NextResponse.json({
		user: { id: user.id, email: user.email, name: user.name },
	});
}
