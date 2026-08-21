import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ knowledgeBaseId: string; sourceId: string }>;
};

export async function GET(
	_request: Request,
	{ params }: Params,
) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, sourceId } =
			await params;
		const upstream = await backendFetch(
			user.accessToken,
			`/knowledge-bases/${knowledgeBaseId}/sources/${sourceId}/file`,
		);
		if (!upstream.ok || !upstream.body) {
			return new NextResponse(
				upstream.body,
				{ status: upstream.status },
			);
		}
		return new NextResponse(upstream.body, {
			status: upstream.status,
			headers: {
				'content-type':
					upstream.headers.get(
						'content-type',
					) ?? 'application/octet-stream',
				'content-disposition':
					upstream.headers.get(
						'content-disposition',
					) ?? 'inline',
			},
		});
	} catch (error) {
		return apiError(error);
	}
}
