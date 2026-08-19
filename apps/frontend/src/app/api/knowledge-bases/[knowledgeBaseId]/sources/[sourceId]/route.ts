import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ knowledgeBaseId: string; sourceId: string }>;
};

export async function DELETE(_request: Request, { params }: Params) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, sourceId } = await params;
		const response = await backendFetch(
			session,
			`/knowledge-bases/${knowledgeBaseId}/sources/${sourceId}`,
			{ method: 'DELETE' },
		);
		if (!response.ok) {
			const body = await response.json().catch(() => ({}));
			return NextResponse.json(body, {
				status: response.status,
			});
		}
		return new NextResponse(null, { status: 204 });
	} catch (error) {
		return apiError(error);
	}
}
