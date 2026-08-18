import 'server-only';

import { NextResponse } from 'next/server';

export async function proxyResponse(response: Response) {
	const body = await response.json().catch(() => ({}));
	return NextResponse.json(body, { status: response.status });
}

export function apiError(error: unknown) {
	return NextResponse.json(
		{
			error:
				error instanceof Error
					? error.message
					: 'The request could not be completed.',
		},
		{ status: 500 },
	);
}
