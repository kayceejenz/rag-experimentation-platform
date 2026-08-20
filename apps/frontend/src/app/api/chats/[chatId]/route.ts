import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError, proxyResponse } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ chatId: string }> };

async function userOrUnauthorized() {
	return getAuthUser();
}

export async function PATCH(request: Request, { params }: Params) {
	const user = await userOrUnauthorized();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { chatId } = await params;
		return proxyResponse(
			await backendFetch(user.accessToken, `/chats/${chatId}`, {
				method: 'PATCH',
				body: JSON.stringify(await request.json()),
			}),
		);
	} catch (error) {
		return apiError(error);
	}
}

export async function DELETE(_request: Request, { params }: Params) {
	const user = await userOrUnauthorized();
	if (!user)
		return NextResponse.json(
			{ error: 'Unauthorized' },
			{ status: 401 },
		);
	try {
		const { chatId } = await params;
		const response = await backendFetch(
			user.accessToken,
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
