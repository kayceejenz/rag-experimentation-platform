'use client';

import {
	createContext,
	ReactNode,
	useCallback,
	useContext,
	useEffect,
	useRef,
	useState,
} from 'react';
import { usePathname } from 'next/navigation';

const NavigationProgressContext = createContext<(() => void) | null>(null);

export function NavigationProgress({ children }: { children: ReactNode }) {
	const pathname = usePathname();
	const [pending, setPending] = useState(false);
	const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

	const startProgress = useCallback(() => {
		setPending(true);
		if (timeoutRef.current) clearTimeout(timeoutRef.current);
		timeoutRef.current = setTimeout(() => setPending(false), 8000);
	}, []);

	useEffect(() => {
		const frame = requestAnimationFrame(() => setPending(false));
		if (timeoutRef.current) clearTimeout(timeoutRef.current);
		return () => cancelAnimationFrame(frame);
	}, [pathname]);

	return (
		<NavigationProgressContext.Provider value={startProgress}>
			<div
				className={`navigation-progress ${pending ? 'active' : ''}`}
				aria-hidden='true'>
				<span />
			</div>
			{children}
		</NavigationProgressContext.Provider>
	);
}

export function useNavigationProgress() {
	return useContext(NavigationProgressContext) ?? (() => undefined);
}
