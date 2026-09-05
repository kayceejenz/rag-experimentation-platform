import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type P = { params: Promise<{ projectId: string }> };

export async function GET(_: Request, { params }: P) {
	const u = await getAuthUser();
	if (!u)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId } = await params;
		return proxyResponse(
			await backendFetch(
				u.accessToken,
				`/projects/${projectId}/prompts`,
			),
		);
	} catch (e) {
		return apiError(e);
	}
}
export async function POST(r: Request, { params }: P) {
	const u = await getAuthUser();
	if (!u)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId } = await params;
		return proxyResponse(
			await backendFetch(
				u.accessToken,
				`/projects/${projectId}/prompts`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify(await r.json()),
				},
			),
		);
	} catch (e) {
		return apiError(e);
	}
}
