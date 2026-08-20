import { NextRequest, NextResponse } from 'next/server';

function hasAccessToken(request: NextRequest): boolean {
	return !!request.cookies.get('access_token')?.value;
}

export function middleware(request: NextRequest) {
	if (!hasAccessToken(request)) {
		const url = request.nextUrl.clone();
		url.pathname = '/auth/signin';
		if (request.nextUrl.pathname !== '/') {
			url.searchParams.set('callbackUrl', request.nextUrl.pathname);
		}
		return NextResponse.redirect(url);
	}
	return NextResponse.next();
}

export const config = {
	matcher: [
		'/((?!auth/|_next/static|_next/image|favicon.ico|api/auth).*)',
	],
};
