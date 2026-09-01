import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ projectId: string }> };

export async function GET(request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
	try {
		const { projectId } = await params;
		const query = new URL(request.url).searchParams;
		const limit = query.get('limit') ?? '50';
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/executions?limit=${encodeURIComponent(limit)}`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
