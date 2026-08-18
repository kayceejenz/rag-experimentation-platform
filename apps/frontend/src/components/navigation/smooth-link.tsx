'use client';

import type { ComponentProps, MouseEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Route } from 'next';

type Props = Omit<ComponentProps<typeof Link>, 'href'> & { href: string };

export function useSmoothNavigation() {
	const router = useRouter();
	return (href: string) => {
		const navigate = () => router.push(href as Route);
		const destination = new URL(href, window.location.href);
		const current = new URL(window.location.href);
		if (
			destination.pathname === current.pathname &&
			destination.search === current.search
		)
			return;

		const reducedMotion = window.matchMedia(
			'(prefers-reduced-motion: reduce)',
		).matches;
		if (!document.startViewTransition || reducedMotion) {
			navigate();
			return;
		}

		const chatToChat =
			current.pathname.startsWith('/chats/') &&
			destination.pathname.startsWith('/chats/');
		document.documentElement.dataset.navigationTransition =
			chatToChat ? 'chat' : 'workspace';
		const transition = document.startViewTransition(navigate);
		void transition.finished.finally(() => {
			delete document.documentElement.dataset
				.navigationTransition;
		});
	};
}

export function SmoothLink({ href, onClick, ...props }: Props) {
	const navigate = useSmoothNavigation();

	function follow(event: MouseEvent<HTMLAnchorElement>) {
		onClick?.(event);
		if (
			event.defaultPrevented ||
			event.button !== 0 ||
			event.metaKey ||
			event.ctrlKey ||
			event.shiftKey ||
			event.altKey
		)
			return;
		event.preventDefault();
		navigate(href);
	}

	return <Link {...props} href={href as Route} onClick={follow} />;
}
