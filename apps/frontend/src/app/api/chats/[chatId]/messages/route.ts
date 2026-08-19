import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ chatId: string }> };

async function forward(
	request: Request | null,
	params: Params['params'],
	method: 'GET' | 'POST',
) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { chatId } = await params;
		const body = request
			? JSON.stringify(await request.json())
			: undefined;
		return proxyResponse(
			await backendFetch(
				session,
				`/chats/${chatId}/messages`,
				{ method, body },
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
