'use client';

import { signOut } from 'next-auth/react';
import { useState } from 'react';
import { LogOut } from 'lucide-react';

export function SignOutButton() {
	const [signingOut, setSigningOut] = useState(false);

	async function handleSignOut() {
		if (signingOut) return;
		setSigningOut(true);

		const result = await signOut({
			callbackUrl: '/auth/signin',
			redirect: false,
		});

		window.location.assign(result.url || '/auth/signin');
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
