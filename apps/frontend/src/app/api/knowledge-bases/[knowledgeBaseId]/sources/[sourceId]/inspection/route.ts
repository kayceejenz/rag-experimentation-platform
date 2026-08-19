import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ knowledgeBaseId: string; sourceId: string }>;
};

export async function GET(_request: Request, { params }: Params) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, sourceId } = await params;
		return proxyResponse(
			await backendFetch(
				session,
				`/knowledge-bases/${knowledgeBaseId}/sources/${sourceId}/inspection`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
