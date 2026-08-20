import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';
import { ProjectPageParams } from '@/types/project';

export async function GET(_request: Request, { params }: ProjectPageParams) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const { projectId } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/chats`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function POST(request: Request, { params }: ProjectPageParams) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const { projectId } = await params;
		const body = await request.json();
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/chats`,
				{
					method: 'POST',
					body: JSON.stringify(body),
				},
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
