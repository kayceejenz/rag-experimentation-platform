'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { MessageComposer } from '@/components/chat/message-composer';
import { MessageList } from '@/components/chat/message-list';
import type { Assistant, Chat, Message, ToolCall } from '@/types/workspace';

type StreamEvent =
	| { type: 'token'; content: string }
	| { type: 'thinking_delta'; content: string }
	| { type: 'tool_step'; tool: ToolCall }
	| { type: 'done'; message: Message; reasoning?: string }
	| { type: 'error'; message: string };

function errorMessage(value: unknown): string {
	if (!value || typeof value !== 'object')
		return 'The request could not be completed.';
	const body = value as { error?: unknown; detail?: unknown };
	const candidate = body.error ?? body.detail;
	if (typeof candidate === 'string') return candidate;
	if (candidate && typeof candidate === 'object') {
		const message = (candidate as { message?: unknown }).message;
		if (typeof message === 'string') return message;
	}
	return 'The request could not be completed.';
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
	const response = await fetch(url, init);
	const body = await response.json().catch(() => null);
	if (!response.ok) throw new Error(errorMessage(body));
	return body as T;
}

export function AssistantPlayground({ assistant }: { assistant: Assistant }) {
	const [conversationId, setConversationId] = useState<string | null>(
		null,
	);
	const [messages, setMessages] = useState<Message[]>([]);
	const [sending, setSending] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [streamingId, setStreamingId] = useState<string | null>(null);
	const [copiedId, setCopiedId] = useState<string | null>(null);
	const endRef = useRef<HTMLDivElement>(null);
	const abortRef = useRef<AbortController | null>(null);

	useEffect(() => {
		endRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages, sending]);

	async function ensureConversation(content: string) {
		if (conversationId) return conversationId;
		const conversation = await requestJson<Chat>(
			`/api/assistants/${assistant.id}/conversations`,
			{
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({
					title:
						content.length > 72
							? `${content.slice(0, 69)}…`
							: content,
				}),
			},
		);
		setConversationId(conversation.id);
		return conversation.id;
	}

	async function send(content: string) {
		const question = content.trim();
		if (!question || sending) return;
		setError(null);
		setSending(true);
		const optimistic: Message = {
			id: `pending-${crypto.randomUUID()}`,
			conversation_id: conversationId ?? 'pending',
			role: 'user',
			content: question,
			citations: [],
			created_at: new Date().toISOString(),
		};
		const assistantId = `streaming-${crypto.randomUUID()}`;
		const assistantPlaceholder: Message = {
			id: assistantId,
			conversation_id: conversationId ?? 'pending',
			role: 'assistant',
			content: '',
			citations: [],
			reasoning: '',
			tool_calls: [],
			created_at: new Date().toISOString(),
		};
		setMessages(current => [
			...current,
			optimistic,
			assistantPlaceholder,
		]);
		setStreamingId(assistantId);
		const controller = new AbortController();
		abortRef.current = controller;
		try {
			const id = await ensureConversation(question);
			const response = await fetch(
				`/api/conversations/${id}/messages/stream`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						content: question,
					}),
					signal: controller.signal,
				},
			);
			if (!response.ok || !response.body) {
				const body = await response
					.json()
					.catch(() => null);
				throw new Error(errorMessage(body));
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			while (true) {
				const { value, done } = await reader.read();
				buffer += decoder.decode(value, {
					stream: !done,
				});
				const frames = buffer.split(/\r?\n\r?\n/);
				buffer = frames.pop() ?? '';
				for (const frame of frames) {
					const data = frame
						.split(/\r?\n/)
						.filter(line =>
							line.startsWith(
								'data:',
							),
						)
						.map(line =>
							line
								.slice(5)
								.trimStart(),
						)
						.join('\n');
					if (!data) continue;
					const event = JSON.parse(
						data,
					) as StreamEvent;
					if (event.type === 'token') {
						setMessages(current =>
							current.map(message =>
								message.id ===
								assistantId
									? {
											...message,
											content:
												message.content +
												event.content,
										}
									: message,
							),
						);
					} else if (
						event.type === 'thinking_delta'
					) {
						setMessages(current =>
							current.map(message =>
								message.id ===
								assistantId
									? {
											...message,
											reasoning:
												(message.reasoning ??
													'') +
												event.content,
										}
									: message,
							),
						);
					} else if (event.type === 'tool_step') {
						setMessages(current =>
							current.map(message => {
								if (
									message.id !==
									assistantId
								)
									return message;
								const tools =
									message.tool_calls ??
									[];
								const exists =
									tools.some(
										tool =>
											tool.id ===
											event
												.tool
												.id,
									);
								return {
									...message,
									tool_calls: exists
										? tools.map(
												tool =>
													tool.id ===
													event
														.tool
														.id
														? event.tool
														: tool,
											)
										: [
												...tools,
												event.tool,
											],
								};
							}),
						);
					} else if (event.type === 'done') {
						setMessages(current =>
							current.map(message =>
								message.id ===
								assistantId
									? {
											...event.message,
											reasoning:
												event.reasoning ??
												message.reasoning,
											tool_calls: [],
										}
									: message,
							),
						);
					} else {
						throw new Error(event.message);
					}
				}
				if (done) break;
			}
		} catch (requestError) {
			if (
				requestError instanceof DOMException &&
				requestError.name === 'AbortError'
			) {
				setMessages(current =>
					current.map(message =>
						message.id === assistantId &&
						!message.content
							? {
									...message,
									content: '_Response stopped._',
								}
							: message,
					),
				);
			} else {
				setMessages(current =>
					current.filter(
						message =>
							message.id !==
							assistantId,
					),
				);
				setError(
					requestError instanceof Error
						? requestError.message
						: 'The assistant could not respond.',
				);
			}
		} finally {
			abortRef.current = null;
			setStreamingId(null);
			setSending(false);
		}
	}

	function submit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const form = event.currentTarget;
		const data = new FormData(form);
		const content = String(data.get('content') ?? '');
		if (!content.trim()) return;
		form.reset();
		void send(content);
	}

	async function copy(message: Message) {
		await navigator.clipboard.writeText(message.content);
		setCopiedId(message.id);
		window.setTimeout(() => setCopiedId(null), 1600);
	}

	return (
		<section
			className='assistant-playground'
			aria-label={`${assistant.name} playground`}>
			<div className='assistant-playground-context'>
				<div>
					<strong>{assistant.name}</strong>
					<span>
						Active revision v
						{assistant.active_revision_version ??
							'—'}
					</span>
				</div>
				<button
					type='button'
					disabled={messages.length === 0}
					onClick={() => {
						abortRef.current?.abort();
						setConversationId(null);
						setMessages([]);
						setError(null);
					}}>
					New conversation
				</button>
			</div>
			<div className='assistant-playground-chat'>
				{error && (
					<div
						className='workspace-error'
						role='alert'>
						{error}
					</div>
				)}
				<MessageList
					messages={messages}
					streamingId={streamingId}
					copiedId={copiedId}
					onCopy={message => void copy(message)}
					onSuggest={send}
					endRef={endRef}
				/>
				<div className='assistant-playground-input'>
					<MessageComposer
						sending={sending}
						placeholder={`Ask ${assistant.name} about its indexed knowledge…`}
						onSubmit={submit}
						onStop={() =>
							abortRef.current?.abort()
						}
					/>
					<p>
						Answers use the active revision
						and may contain mistakes.
					</p>
				</div>
			</div>
		</section>
	);
}
