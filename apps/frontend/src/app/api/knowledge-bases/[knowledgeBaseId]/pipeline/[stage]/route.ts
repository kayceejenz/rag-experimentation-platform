import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ knowledgeBaseId: string; stage: string }> };
export async function POST(_request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, stage } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/knowledge-bases/${knowledgeBaseId}/pipeline/${stage}`,
				{ method: 'POST' },
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
