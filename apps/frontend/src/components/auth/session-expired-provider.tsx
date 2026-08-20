'use client';

import {
	createContext,
	useContext,
	useState,
	useCallback,
	ReactNode,
} from 'react';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface SessionExpiredContextValue {
	showSessionExpired: () => void;
}

const SessionExpiredContext =
	createContext<SessionExpiredContextValue>({
		showSessionExpired: () => {},
	});

export function useSessionExpired() {
	return useContext(SessionExpiredContext);
}

export function SessionExpiredProvider({
	children,
}: {
	children: ReactNode;
}) {
	const [open, setOpen] = useState(false);

	const showSessionExpired = useCallback(() => {
		setOpen(true);
	}, []);

	async function handleGoToLogin() {
		await fetch('/api/auth/logout', { method: 'POST' }).catch(() => undefined);
		const callbackUrl = `${window.location.pathname}${window.location.search}`;
		window.location.replace(
			`/auth/signin?error=SessionExpired&callbackUrl=${encodeURIComponent(callbackUrl)}`,
		);
	}

	return (
		<SessionExpiredContext.Provider
			value={{ showSessionExpired }}>
			{children}
			{open && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'
					aria-labelledby='session-expired-title'>
					<section className='workspace-modal session-expired-modal'>
						<div className='session-expired-icon'>
							<AlertTriangle size={28} />
						</div>
						<div className='modal-title'>
							<div>
								<h2 id='session-expired-title'>
									Session
									expired
								</h2>
								<p className='session-expired-desc'>
									Your
									sign-in
									session
									has
									expired.
									Please
									sign
									in
									again
									to
									continue.
								</p>
							</div>
						</div>
						<div className='project-form-actions'>
							<button
								type='button'
								className='primary-action'
								onClick={
									handleGoToLogin
								}>
								Go
								to
								login
								<ArrowRight
									size={
										16
									}
								/>
							</button>
						</div>
					</section>
				</div>
			)}
		</SessionExpiredContext.Provider>
	);
}