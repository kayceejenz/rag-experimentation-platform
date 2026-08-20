'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

type Theme = 'light' | 'dark';

export function ThemeToggle({ disabled }: { disabled?: boolean } = {}) {
	const [theme, setTheme] = useState<Theme>('light');

	useEffect(() => {
		const storedTheme = window.localStorage.getItem(
			'theme',
		) as Theme | null;
		const preferredTheme = window.matchMedia(
			'(prefers-color-scheme: dark)',
		).matches
			? 'dark'
			: 'light';
		const initialTheme = storedTheme ?? preferredTheme;
		setTheme(initialTheme);
		document.documentElement.dataset.theme = initialTheme;
	}, []);

	function toggleTheme() {
		const nextTheme = theme === 'light' ? 'dark' : 'light';
		setTheme(nextTheme);
		document.documentElement.dataset.theme = nextTheme;
		window.localStorage.setItem('theme', nextTheme);
	}

	return (
		<button
			className='theme-toggle'
			type='button'
			onClick={toggleTheme}
			disabled={disabled}
			aria-label='Toggle color theme'>
			{theme === 'light' ? (
				<Moon size={18} aria-hidden />
			) : (
				<Sun size={18} aria-hidden />
			)}
		</button>
	);
}
