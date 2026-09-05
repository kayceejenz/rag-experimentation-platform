import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import { ClientProviders } from '@/components/auth/client-providers';
import { AppVersion } from '@/components/layout/app-version';
import './globals.css';
import './experiment-overrides.css';

const font = Outfit({
	subsets: ['latin'],
	weight: ['400', '500', '600', '700'],
	variable: '--font-app',
	display: 'swap',
});

export const metadata: Metadata = {
	title: 'kayceejenz.ai',
	description: 'Your AI assistant',
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang='en' className={font.variable}>
			<body>
				<ClientProviders>
					{children}
				</ClientProviders>
				<AppVersion />
			</body>
		</html>
	);
}
