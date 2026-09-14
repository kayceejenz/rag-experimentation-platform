import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type P = { params: Promise<{ projectId: string; experimentId: string }> };

export async function POST(request: Request, { params }: P) {
	const u = await getAuthUser();
	if (!u)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId, experimentId } = await params;
		const body = await request.text();
		return proxyResponse(
			await backendFetch(
				u.accessToken,
				`/projects/${projectId}/experiments/${experimentId}/runs`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body,
				},
			),
		);
	} catch (e) {
		return apiError(e);
	}
}
