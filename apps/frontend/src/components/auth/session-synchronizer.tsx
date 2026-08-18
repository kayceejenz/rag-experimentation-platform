'use client';

import { getSession } from 'next-auth/react';
import { useEffect } from 'react';

export function SessionSynchronizer() {
	useEffect(() => {
		void getSession().then(session => {
			if (session?.error === 'RefreshAccessTokenError') {
				const callbackUrl = `${window.location.pathname}${window.location.search}`;
				window.location.replace(
					`/auth/signin?error=SessionExpired&callbackUrl=${encodeURIComponent(callbackUrl)}`,
				);
			}
		});
	}, []);

	return null;
}
