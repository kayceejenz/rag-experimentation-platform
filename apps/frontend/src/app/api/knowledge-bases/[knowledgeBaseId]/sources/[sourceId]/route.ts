import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ knowledgeBaseId: string; sourceId: string }>;
};

export async function DELETE(_request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, sourceId } = await params;
		const response = await backendFetch(
			user.accessToken,
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
