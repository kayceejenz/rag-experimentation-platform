'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const ERROR_MESSAGES: Record<string, { title: string; description: string }> = {
	Configuration: {
		title: 'Server configuration error',
		description:
			'There is a problem with the server authentication configuration. Please contact the administrator.',
	},
	DatabaseError: {
		title: 'Database connection error',
		description:
			'Could not connect to the database during sign-in. Please try again in a moment.',
	},
	Default: {
		title: 'Authentication error',
		description:
			'An unexpected authentication error occurred. Please try again.',
	},
};

function AuthErrorContent() {
	const searchParams = useSearchParams();
	const errorCode = searchParams.get('error') ?? 'Default';
	const { title, description } =
		ERROR_MESSAGES[errorCode] ?? ERROR_MESSAGES.Default;

	return (
		<main className='auth-error-page'>
			<section className='auth-error-card panel'>
				<div className='auth-error-icon'>
					<ShieldAlert size={27} />
				</div>
				<h1>{title}</h1>
				<p>{description}</p>
				<div className='auth-error-actions'>
					<Link
						href='/auth/signin'
						className='primary-action'>
						Try signing in again
					</Link>
					<Link
						href='/'
						className='auth-back-link'>
						<ArrowLeft size={15} />
						Back to home
					</Link>
				</div>
			</section>
		</main>
	);
}

export default function AuthErrorPage() {
	return (
		<Suspense>
			<AuthErrorContent />
		</Suspense>
	);
}
