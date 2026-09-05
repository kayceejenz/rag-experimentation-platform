import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';
type Params = { params: Promise<{ projectId: string; indexId: string }> };
export async function GET(_request: Request, { params }: Params) {
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
				`/projects/${projectId}/indexes/${indexId}`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
export async function DELETE(_request: Request, { params }: Params) {
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
				`/projects/${projectId}/indexes/${indexId}`,
				{ method: 'DELETE' },
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
