import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import './globals.css';

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
			<body>{children}</body>
		</html>
	);
}
