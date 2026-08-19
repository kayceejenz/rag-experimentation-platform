import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendFetch } from '@/lib/api/backend';
import { apiError } from '@/lib/api/proxy-response';

type Params = { params: Promise<{ chatId: string }> };

export async function POST(request: Request, { params }: Params) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id || session.error) {
		return NextResponse.json(
			{ error: 'Your session expired. Sign in again.' },
			{ status: 401 },
		);
	}
	try {
		const { chatId } = await params;
		const response = await backendFetch(
			session,
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
