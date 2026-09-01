import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ knowledgeBaseId: string }> };
export async function GET(_request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/knowledge-bases/${knowledgeBaseId}/pipeline`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
