import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ projectId: string; datasetId: string }>;
};

export async function GET(_: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
	try {
		const { projectId, datasetId } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/benchmarks/${datasetId}`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
