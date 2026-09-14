import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = {
	params: Promise<{ knowledgeBaseId: string; sourceId: string }>;
};

export async function GET(request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { knowledgeBaseId, sourceId } = await params;
		const upstream = await backendFetch(
			user.accessToken,
			`/knowledge-bases/${knowledgeBaseId}/sources/${sourceId}/file`,
			{
				headers: request.headers.has('range')
					? {
							range: request.headers.get(
								'range',
							)!,
						}
					: undefined,
			},
		);
		if (!upstream.ok || !upstream.body) {
			return new NextResponse(upstream.body, {
				status: upstream.status,
			});
		}
		const contentType =
			upstream.headers.get('content-type') ??
			'application/octet-stream';
		const headers = new Headers({
			'content-type': contentType,
			'content-disposition':
				upstream.headers.get('content-disposition') ??
				'inline',
			'x-content-type-options': 'nosniff',
		});
		for (const name of [
			'accept-ranges',
			'content-length',
			'content-range',
			'etag',
			'last-modified',
		]) {
			const value = upstream.headers.get(name);
			if (value) headers.set(name, value);
		}
		if (contentType !== 'application/pdf') {
			headers.set(
				'content-security-policy',
				"sandbox; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'",
			);
		}
		return new NextResponse(upstream.body, {
			status: upstream.status,
			headers,
		});
	} catch (error) {
		return apiError(error);
	}
}
