import Link from 'next/link';

export default function NotFound() {
	return (
		<main style={{ display: 'grid', placeItems: 'center', minHeight: '100dvh', padding: 24, textAlign: 'center' }}>
			<div>
				<h1 style={{ fontSize: 48, fontWeight: 700, marginBottom: 8 }}>404</h1>
				<p style={{ color: 'var(--muted)', marginBottom: 24 }}>This page doesn&apos;t exist.</p>
				<Link
					href='/'
					style={{
						display: 'inline-flex',
						alignItems: 'center',
						gap: 8,
						padding: '10px 20px',
						borderRadius: 8,
						background: 'var(--accent)',
						color: 'white',
						fontWeight: 600,
						textDecoration: 'none',
					}}>
					Go to chat
				</Link>
			</div>
		</main>
	);
}
