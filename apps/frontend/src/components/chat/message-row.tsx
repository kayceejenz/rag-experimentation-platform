'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Check, Copy, User, ChevronDown, BookOpen } from 'lucide-react';
import type { Message } from '@/types/workspace';
import { CitationFootnotes } from './citation-footnotes';
import { ToolCallSteps } from './tool-call-step';

function MarkdownContent({ content }: { content: string }) {
	return (
		<ReactMarkdown
			remarkPlugins={[remarkGfm]}
			components={{
				a: ({ children, ...props }) => (
					<a
						{...props}
						target='_blank'
						rel='noreferrer'>
						{children}
					</a>
				),
			}}>
			{content}
		</ReactMarkdown>
	);
}

function ReasoningBlock({
	reasoning,
	isStreaming,
}: {
	reasoning: string;
	isStreaming: boolean;
}) {
	return (
		<details
			className='reasoning-block'
			open={isStreaming && !reasoning}>
			<summary>
				<ChevronDown
					size={13}
					className='reasoning-chevron'
				/>
				<span>
					{isStreaming && !reasoning
						? 'Thinking…'
						: 'Reasoning'}
				</span>
			</summary>
			{reasoning && (
				<div className='reasoning-body'>
					{reasoning}
				</div>
			)}
		</details>
	);
}

export function MessageRow({
	message,
	streamingId,
	copiedId,
	onCopy,
}: {
	message: Message;
	streamingId: string | null;
	copiedId: string | null;
	onCopy: (message: Message) => void;
}) {
	const isAssistant = message.role === 'assistant';
	const isStreaming = message.id === streamingId;
	const hasToolCalls =
		isAssistant &&
		message.tool_calls &&
		message.tool_calls.length > 0;
	const hasReasoning =
		isAssistant && (isStreaming || !!message.reasoning);
	const hasCitations = isAssistant && message.citations.length > 0;
	const [showCitations, setShowCitations] = useState(false);

	return (
		<article className={`message-row ${message.role}`}>
			<div className='message-avatar'>
				{isAssistant ? (
					<Bot size={17} />
				) : (
					<User size={17} />
				)}
			</div>
			<div className='message-body'>
				<div className='message-meta'>
					<strong>
						{isAssistant
							? 'AI Assistant'
							: 'You'}
					</strong>
					<time>
						{new Intl.DateTimeFormat(
							undefined,
							{
								hour: '2-digit',
								minute: '2-digit',
							},
						).format(
							new Date(
								message.created_at,
							),
						)}
					</time>
				</div>
				{isAssistant ? (
					<div className='message-markdown'>
						<MarkdownContent
							content={
								message.content
							}
						/>
						{isStreaming && (
							<span
								className='streaming-cursor'
								aria-label='Generating'
							/>
						)}
					</div>
				) : (
					<p>{message.content}</p>
				)}
				{hasReasoning && (
					<ReasoningBlock
						reasoning={
							message.reasoning ?? ''
						}
						isStreaming={isStreaming}
					/>
				)}
				{hasToolCalls && (
					<ToolCallSteps
						steps={message.tool_calls!}
					/>
				)}
				{hasCitations && showCitations && (
					<CitationFootnotes
						citations={message.citations}
					/>
				)}
				{isAssistant && !isStreaming && (
					<div className='message-actions'>
						{hasCitations && (
							<button
								type='button'
								className={`citation-toggle ${showCitations ? 'active' : ''}`}
								onClick={() =>
									setShowCitations(
										prev =>
											!prev,
									)
								}
								aria-label={
									showCitations
										? 'Hide sources'
										: 'Show sources'
								}>
								<BookOpen
									size={
										13
									}
								/>
								<span>
									{showCitations
										? 'Hide sources'
										: 'Show sources'}
								</span>
							</button>
						)}
						<button
							type='button'
							onClick={() =>
								onCopy(message)
							}
							aria-label='Copy response'>
							{copiedId ===
							message.id ? (
								<>
									<Check
										size={
											14
										}
									/>
									Copied
								</>
							) : (
								<>
									<Copy
										size={
											14
										}
									/>
									Copy
								</>
							)}
						</button>
					</div>
				)}
			</div>
		</article>
	);
}
