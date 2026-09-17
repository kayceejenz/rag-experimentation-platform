'use client';

import { Library, Menu, X } from 'lucide-react';

export function ChatHeader({
	title,
	sourcesOpen,
	sourcesCount,
	onToggleSources,
	onOpenSidebar,
}: {
	title: string;
	sourcesOpen: boolean;
	sourcesCount: number;
	onToggleSources: () => void;
	onOpenSidebar: () => void;
}) {
	return (
		<header className='chat-page-header'>
			<button
				className='mobile-chat-menu'
				type='button'
				onClick={onOpenSidebar}
				aria-label='Open chats'>
				<Menu size={18} />
			</button>
			<div className='editorial-chat-title'>
				<h1>{title}</h1>
			</div>
			<button
				type='button'
				className='header-sources-toggle'
				onClick={onToggleSources}>
				{sourcesOpen ? (
					<>
						<X size={14} />
						Knowledge Base
					</>
				) : (
					<>
						<Library size={15} />
						Knowledge Base
						{sourcesCount > 0 && (
							<span className='sources-badge'>
								{sourcesCount}
							</span>
						)}
					</>
				)}
			</button>
		</header>
	);
}
