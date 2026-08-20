'use client';

import { useSearchParams } from 'next/navigation';
import { FormEvent, Suspense, useEffect, useState } from 'react';
import { CircleAlert, LoaderCircle } from 'lucide-react';
import { ThemeToggle } from '@/components/theme/theme-toggle';

const ERROR_COPY: Record<string, string> = {
	SessionExpired: 'Your session expired. Sign in again to continue.',
	InvalidCredentials: 'The email or password is incorrect.',
	Default: 'Something went wrong. Please try again.',
};

function SignInContent() {
	const params = useSearchParams();
	const requestedCallback = params.get('callbackUrl') ?? '/';
	const callbackUrl =
		requestedCallback.startsWith('/') &&
		!requestedCallback.startsWith('//')
			? requestedCallback
			: '/';
	const initialError = params.get('error');
	const [mode, setMode] = useState<'signin' | 'register'>('signin');
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [displayName, setDisplayName] = useState('');
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(
		initialError
			? (ERROR_COPY[initialError] ?? ERROR_COPY.Default)
			: '',
	);

	useEffect(() => {
		void fetch('/api/auth/me')
			.then(r => r.ok ? r.json() : null)
			.then(data => {
				if (data?.user) window.location.replace(callbackUrl);
			})
			.catch(() => undefined);
	}, [callbackUrl]);

	function changeMode(next: 'signin' | 'register') {
		setMode(next);
		setError('');
	}

	async function submit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setLoading(true);
		setError('');
		try {
			if (mode === 'register') {
				const response = await fetch(
					'/api/account/register',
					{
						method: 'POST',
						headers: {
							'content-type':
								'application/json',
						},
						body: JSON.stringify({
							email,
							password,
							display_name:
								displayName.trim() ||
								null,
						}),
					},
				);
				const body = (await response
					.json()
					.catch(() => ({}))) as {
					detail?: string;
					error?: {
						message?: string;
						details?: Array<{
							message?: string;
						}>;
					};
				};
				if (!response.ok) {
					throw new Error(
						body.error?.details?.[0]
							?.message ??
							body.error?.message ??
							body.detail ??
							'Unable to create the account.',
					);
				}
			}

			const response = await fetch('/api/auth/login', {
				method: 'POST',
				headers: {
					'content-type': 'application/json',
				},
				body: JSON.stringify({ email, password }),
			});
			const body = await response.json().catch(() => ({}));
			if (!response.ok) {
				throw new Error(
					(body as { error?: string }).error ??
					'The email or password is incorrect.',
				);
			}
			window.location.replace(callbackUrl);
		} catch (cause) {
			setError(
				cause instanceof Error
					? cause.message
					: ERROR_COPY.Default,
			);
		} finally {
			setLoading(false);
		}
	}

	return (
		<main className='signin-page'>
			<div className='signin-decoration' />
			<section
				className='signin-card'
				aria-busy={loading || undefined}
				aria-labelledby='signin-title'>
				<div className='signin-card-header'>
					<div className='signin-brand'>
						<span className='signin-brand-text'>
							kayceejenz.ai
						</span>
					</div>
					<ThemeToggle disabled={loading} />
				</div>

				<div className='signin-copy'>
					<h1 id='signin-title'>
						{mode === 'signin'
							? 'Welcome back'
							: 'Create your account'}
					</h1>
					<p>
						{mode === 'signin'
							? 'Sign in to continue to your assistant.'
							: 'Get started in minutes.'}
					</p>
				</div>

				<div
					className='auth-tabs'
					role='tablist'
					aria-label='Authentication mode'>
					<button
						type='button'
						role='tab'
						aria-selected={
							mode === 'signin'
						}
						className={
							mode === 'signin'
								? 'active'
								: ''
						}
						onClick={() =>
							changeMode('signin')
						}>
						Sign in
					</button>
					<button
						type='button'
						role='tab'
						aria-selected={
							mode === 'register'
						}
						className={
							mode === 'register'
								? 'active'
								: ''
						}
						onClick={() =>
							changeMode('register')
						}>
						Create account
					</button>
				</div>

				{error && (
					<div
						className='signin-error'
						role='alert'>
						<CircleAlert
							size={15}
							aria-hidden
						/>
						<span>{error}</span>
					</div>
				)}

			<form className='auth-form' onSubmit={submit}>
				{mode === 'register' && (
					<label>
						<span>
							Display name
						</span>
						<input
							autoComplete='name'
							value={
								displayName
							}
							disabled={loading}
							onChange={event =>
								setDisplayName(
									event
										.target
										.value,
								)
							}
							maxLength={160}
							placeholder='Optional'
						/>
					</label>
				)}
				<label>
					<span>Email</span>
					<input
						type='email'
						autoComplete='email'
						value={email}
						required
						disabled={loading}
						onChange={event =>
							setEmail(
								event
									.target
									.value,
							)
						}
						placeholder='you@example.com'
					/>
				</label>
				<label>
					<span>Password</span>
					<input
						type='password'
						autoComplete={
							mode ===
							'signin'
								? 'current-password'
								: 'new-password'
						}
						value={password}
						required
						disabled={loading}
						minLength={
								mode ===
								'register'
									? 12
									: 1
							}
							onChange={event =>
								setPassword(
									event
										.target
										.value,
								)
							}
							placeholder='••••••••••••'
						/>
						{mode === 'register' && (
							<small>
								At least 12 characters.
							</small>
						)}
					</label>
					<button
						type='submit'
						className='auth-submit'
						disabled={loading}>
						{loading && (
							<LoaderCircle
								className='signin-spin'
								size={16}
								aria-hidden
							/>
						)}
						{loading
							? 'Please wait…'
							: mode === 'signin'
								? 'Sign in'
								: 'Create account'}
					</button>
				</form>
			</section>
		</main>
	);
}

export default function SignInPage() {
	return (
		<Suspense>
			<SignInContent />
		</Suspense>
	);
}
