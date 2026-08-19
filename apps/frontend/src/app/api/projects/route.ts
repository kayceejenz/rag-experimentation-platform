import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

export async function GET() {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		return proxyResponse(await backendFetch(session, '/projects'));
	} catch (error) {
		return apiError(error);
	}
}

export async function POST(request: Request) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const body = await request.json();
		return proxyResponse(
			await backendFetch(session, '/projects', {
				method: 'POST',
				body: JSON.stringify(body),
			}),
		);
	} catch (error) {
		return apiError(error);
	}
}
