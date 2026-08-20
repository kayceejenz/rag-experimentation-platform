import { NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/api/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ chatId: string }> };

export async function POST(request: Request, { params }: Params) {
	const user = await getAuthUser();
	if (!user) {
		return NextResponse.json(
			{ error: 'Your session expired. Sign in again.' },
			{ status: 401 },
		);
	}
	try {
		const { chatId } = await params;
		const response = await backendFetch(
			user.accessToken,
			`/chats/${chatId}/messages/stream`,
			{
				method: 'POST',
				body: JSON.stringify(await request.json()),
				signal: request.signal,
			},
		);
		if (!response.ok || !response.body) {
			const body = await response.json().catch(() => ({}));
			return NextResponse.json(body, {
				status: response.status,
			});
		}
		return new Response(response.body, {
			status: response.status,
			headers: {
				'content-type':
					'text/event-stream; charset=utf-8',
				'cache-control': 'no-cache, no-transform',
				'x-accel-buffering': 'no',
			},
		});
	} catch (error) {
		return apiError(error);
	}
}
