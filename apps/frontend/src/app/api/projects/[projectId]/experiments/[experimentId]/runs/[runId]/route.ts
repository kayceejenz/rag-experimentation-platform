import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type P = {
	params: Promise<{
		projectId: string;
		experimentId: string;
		runId: string;
	}>;
};

export async function GET(_: Request, { params }: P) {
	const u = await getAuthUser();
	if (!u)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId, experimentId, runId } = await params;
		return proxyResponse(
			await backendFetch(
				u.accessToken,
				`/projects/${projectId}/experiments/${experimentId}/runs/${runId}`,
			),
		);
	} catch (e) {
		return apiError(e);
	}
}
