import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

export async function GET(
	_request: Request,
	context: {
		params: Promise<{
			projectId: string;
			indexId: string;
			artifactId: string;
		}>;
	},
) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId, indexId, artifactId } = await context.params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/indexes/${indexId}/artifacts/${artifactId}/preview`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
