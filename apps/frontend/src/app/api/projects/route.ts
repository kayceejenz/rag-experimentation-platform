import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

export async function GET() {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		return proxyResponse(
			await backendFetch(user.accessToken, '/projects'),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function POST(request: Request) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const body = await request.json();
		return proxyResponse(
			await backendFetch(user.accessToken, '/projects', {
				method: 'POST',
				body: JSON.stringify(body),
			}),
		);
	} catch (error) {
		return apiError(error);
	}
}
