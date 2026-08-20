import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ knowledgeBaseId: string }> };

async function userOrUnauthorized() {
	const user = await getAuthUser();
	return user;
}

export async function GET(_request: Request, { params }: Params) {
	const user = await userOrUnauthorized();
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
				`/knowledge-bases/${knowledgeBaseId}/sources`,
			),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function POST(request: Request, { params }: Params) {
	const user = await userOrUnauthorized();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId } = await params;
		const form = await request.formData();
		const file = form.get('file');
		if (!(file instanceof File)) {
			return NextResponse.json(
				{ error: 'Select a file to upload.' },
				{ status: 400 },
			);
		}
		if (file.size > 5 * 1024 * 1024) {
			return NextResponse.json(
				{ error: 'File size must not exceed 5 MB.' },
				{ status: 413 },
			);
		}
		const upstream = new FormData();
		upstream.set('file', file);
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/knowledge-bases/${knowledgeBaseId}/sources`,
				{
					method: 'POST',
					body: upstream,
				},
			),
		);
	} catch (error) {
		return apiError(error);
	}
}
