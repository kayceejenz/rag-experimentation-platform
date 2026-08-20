'use client';

import { ReactNode } from 'react';
import {
	SessionExpiredProvider,
} from '@/components/auth/session-expired-provider';

export function ClientProviders({
	children,
}: {
	children: ReactNode;
}) {
	return (
		<SessionExpiredProvider>
			{children}
		</SessionExpiredProvider>
	);
}