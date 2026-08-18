import 'server-only';

import type { Session } from 'next-auth';
import { serverEnv } from '@/lib/env';

type BackendRequest = Omit<RequestInit, 'headers'> & {
	headers?: HeadersInit;
};

export async function backendFetch(
	session: Session,
	path: string,
	req: BackendRequest = {},
): Promise<Response> {
	if (!session.user?.id || !session.accessToken) {
		throw new Error(
			'An authenticated user is required for backend requests.',
		);
	}

	const headers = new Headers(req.headers);
	headers.set('authorization', `Bearer ${session.accessToken}`);
	if (
		req.body &&
		!(req.body instanceof FormData) &&
		!headers.has('content-type')
	) {
		headers.set('content-type', 'application/json');
	}

	return fetch(`${serverEnv.BACKEND_API_URL}/api/v1${path}`, {
		...req,
		headers,
		cache: req.cache ?? 'no-store',
	});
}

export async function backendJson<T>(
	session: Session,
	path: string,
	init: BackendRequest = {},
): Promise<T> {
	const response = await backendFetch(session, path, init);
	const body = (await response.json().catch(() => ({}))) as T & {
		detail?: string;
		error?: { message?: string };
	};
	if (!response.ok) {
		throw new Error(
			body.error?.message ??
				body.detail ??
				`Backend request failed with status ${response.status}.`,
		);
	}
	return body;
}
