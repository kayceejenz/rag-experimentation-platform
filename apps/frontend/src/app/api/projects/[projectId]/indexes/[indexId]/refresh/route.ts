import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ projectId: string; indexId: string }> };

export async function POST(request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId, indexId } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/indexes/${indexId}/refresh`,
				{ method: 'POST', body: await request.text() },
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
