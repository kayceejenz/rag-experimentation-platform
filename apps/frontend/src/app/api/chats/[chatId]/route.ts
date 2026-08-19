import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ chatId: string }> };

async function sessionOrUnauthorized() {
	const session = await getServerSession(authOptions);
	return session?.user?.id && !session.error ? session : null;
}

export async function PATCH(request: Request, { params }: Params) {
	const session = await sessionOrUnauthorized();
	if (!session)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { chatId } = await params;
		return proxyResponse(
			await backendFetch(session, `/chats/${chatId}`, {
				method: 'PATCH',
				body: JSON.stringify(await request.json()),
			}),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function DELETE(_request: Request, { params }: Params) {
	const session = await sessionOrUnauthorized();
	if (!session)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { chatId } = await params;
		const response = await backendFetch(
			session,
			`/chats/${chatId}`,
			{ method: 'DELETE' },
		);
		if (response.status === 204)
			return new Response(null, { status: 204 });
		return proxyResponse(response);
	} catch (error) {
		return apiError(error);
	}
}
