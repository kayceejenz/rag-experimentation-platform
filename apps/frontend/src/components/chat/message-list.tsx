'use client';

import { RefObject } from 'react';
import { Sparkles, FileText, MessageCircle, BookOpen } from 'lucide-react';
import type { Message } from '@/types/workspace';
import { MessageRow } from './message-row';

const SUGGESTIONS = [
	{ icon: FileText, label: 'Summarize my documents', prompt: 'Summarize the key points from all uploaded documents.' },
	{ icon: MessageCircle, label: 'Explain a concept', prompt: 'Explain the main concept covered in my sources.' },
	{ icon: BookOpen, label: 'Find insights', prompt: 'What are the most important insights from my documents?' },
];

export function MessageList({
	messages,
	streamingId,
	copiedId,
	onCopy,
	onSuggest,
	endRef,
}: {
	messages: Message[];
	streamingId: string | null;
	copiedId: string | null;
	onCopy: (message: Message) => void;
	onSuggest: (content: string) => Promise<void>;
	endRef: RefObject<HTMLDivElement | null>;
}) {
	return (
		<div className='conversation-messages'>
			{messages.length === 0 && (
				<div className='conversation-empty'>
					<div className='empty-glow' />
					<div className='empty-icon-large'>
						<Sparkles size={32} />
					</div>
					<h2>What can I help with?</h2>
					<p>
						Ask anything about your uploaded documents,
						or try a suggestion below.
					</p>
					<div className='empty-suggestions'>
						{SUGGESTIONS.map(s => (
							<button
								key={s.label}
								className='suggestion-chip'
								onClick={() => onSuggest(s.prompt)}
							>
								<s.icon size={15} />
								<span>{s.label}</span>
							</button>
						))}
					</div>
				</div>
			)}
			{messages.map(message => (
				<MessageRow
					key={message.id}
					message={message}
					streamingId={streamingId}
					copiedId={copiedId}
					onCopy={onCopy}
				/>
			))}
			<div ref={endRef} />
		</div>
	);
}
