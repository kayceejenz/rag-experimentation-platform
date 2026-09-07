'use client';

import { ReactNode } from 'react';
import { SessionExpiredProvider } from '@/components/auth/session-expired-provider';
import { NavigationProgress } from '@/components/navigation/navigation-progress';

export function ClientProviders({ children }: { children: ReactNode }) {
	return (
		<SessionExpiredProvider>
			<NavigationProgress>{children}</NavigationProgress>
		</SessionExpiredProvider>
	);
}
