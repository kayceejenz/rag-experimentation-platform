import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';
import { ProjectPageParams } from '@/types/project';

export async function GET(_request: Request, { params }: ProjectPageParams) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const { projectId } = await params;
		return proxyResponse(
			await backendFetch(
				session,
				`/projects/${projectId}/chats`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function POST(request: Request, { params }: ProjectPageParams) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);

	try {
		const { projectId } = await params;
		const body = await request.json();
		return proxyResponse(
			await backendFetch(
				session,
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
