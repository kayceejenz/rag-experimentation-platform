import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ projectId: string }> };

async function forward(
	request: Request | null,
	params: Params['params'],
	method: 'GET' | 'POST',
) {
	const user = await getAuthUser();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { projectId } = await params;
		return proxyResponse(
			await backendFetch(
				user.accessToken,
				`/projects/${projectId}/assistants`,
				{
					method,
					body: request
						? JSON.stringify(
								await request.json(),
							)
						: undefined,
				},
			),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function GET(_request: Request, { params }: Params) {
	return forward(null, params, 'GET');
}
export async function POST(request: Request, { params }: Params) {
	return forward(request, params, 'POST');
}
