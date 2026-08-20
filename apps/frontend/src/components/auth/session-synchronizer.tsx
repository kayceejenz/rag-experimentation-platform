'use client';

import { useEffect } from 'react';
import { useSessionExpired } from '@/components/auth/session-expired-provider';

export function SessionSynchronizer() {
	const { showSessionExpired } = useSessionExpired();

	useEffect(() => {
		void fetch('/api/auth/me')
			.then(r => {
				if (r.status === 401) showSessionExpired();
			})
			.catch(() => undefined);
	}, [showSessionExpired]);

	return null;
}
