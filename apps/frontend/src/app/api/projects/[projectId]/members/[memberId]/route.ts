import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ projectId: string; memberId: string }> };

export async function PUT(request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
	try {
		const { projectId, memberId } = await params;
		return proxyResponse(await backendFetch(user.accessToken, `/projects/${projectId}/members/${memberId}`, { method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify(await request.json()) }));
	} catch (error) { return apiError(error); }
}

export async function DELETE(_request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
	try {
		const { projectId, memberId } = await params;
		return proxyResponse(await backendFetch(user.accessToken, `/projects/${projectId}/members/${memberId}`, { method: 'DELETE' }));
	} catch (error) { return apiError(error); }
}
