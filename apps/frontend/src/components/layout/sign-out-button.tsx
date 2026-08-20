'use client';

import { useState } from 'react';
import { LogOut } from 'lucide-react';

export function SignOutButton() {
	const [signingOut, setSigningOut] = useState(false);

	async function handleSignOut() {
		if (signingOut) return;
		setSigningOut(true);
		await fetch('/api/auth/logout', { method: 'POST' }).catch(() => undefined);
		window.location.assign('/auth/signin');
	}

	return (
		<button
			onClick={() => void handleSignOut()}
			className='rail-user-signout'
			disabled={signingOut}
			title='Sign out'
			type='button'>
			<LogOut size={14} aria-hidden />
		</button>
	);
}
