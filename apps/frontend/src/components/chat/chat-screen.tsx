'use client';

import {
	ChangeEvent,
	FormEvent,
	KeyboardEvent,
	useEffect,
	useRef,
	useState,
} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
	ArrowLeft,
	ArrowUp,
	Check,
	ChevronDown,
	ChevronRight,
	CircleAlert,
	CircleCheck,
	Copy,
	Ellipsis,
	FileText,
	Files,
	Folder,
	LoaderCircle,
	Menu,
	MessageSquareText,
	PanelLeftClose,
	PanelLeftOpen,
	PanelRightOpen,
	Paperclip,
	PencilLine,
	Plus,
	ScanEye,
	Square,
	Trash,
	Upload,
	User,
	X,
} from 'lucide-react';
import type {
	Chat,
	Message,
	Source,
	SourceInspection,
} from '@/types/workspace';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import { SessionSynchronizer } from '@/components/auth/session-synchronizer';
import {
	SmoothLink,
	useSmoothNavigation,
} from '@/components/navigation/smooth-link';
import { ChatScreenProps } from '@/types/chat-screen';

async function json<T>(url: string, init?: RequestInit): Promise<T> {
	const response = await fetch(url, init);
	const body = (await response.json().catch(() => ({}))) as T & {
		error?: string | { message?: string };
		detail?: string | { message?: string };
	};
	if (!response.ok) {
		const detail =
			typeof body.detail === 'string'
				? body.detail
				: body.detail?.message;
		const error =
			typeof body.error === 'string'
				? body.error
				: body.error?.message;
		throw new Error(
			error ??
				detail ??
				'The request could not be completed.',
		);
	}
	return body;
}

const activeStatuses = new Set(['uploaded', 'queued', 'processing']);
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

function formatBytes(bytes: number) {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function OcrElementCard({
	element,
}: {
	element: SourceInspection['elements'][number];
}) {
	return (
		<article className='element-record'>
			<header>
				<span className='element-sequence'>
					{element.sequence_number + 1}
				</span>
				<div>
					<strong>{element.category}</strong>
					<small>
						{element.page_number
							? `Page ${element.page_number}`
							: 'No page'}
					</small>
				</div>
			</header>
			<p>
				{element.content ||
					'No text extracted for this element.'}
			</p>
			{element.coordinates != null && (
				<div className='record-metadata'>
					<strong>Coordinates</strong>
					<pre>
						{JSON.stringify(
							element.coordinates,
							null,
							2,
						)}
					</pre>
				</div>
			)}
			{Object.keys(element.metadata).length > 0 && (
				<div className='record-metadata'>
					<strong>Metadata</strong>
					<pre>
						{JSON.stringify(
							element.metadata,
							null,
							2,
						)}
					</pre>
				</div>
			)}
			{element.table_html && (
				<div className='record-metadata'>
					<strong>Extracted table HTML</strong>
					<pre>{element.table_html}</pre>
				</div>
			)}
		</article>
	);
}

function RagChunkCard({
	chunk,
}: {
	chunk: SourceInspection['chunks'][number];
}) {
	const approximateTokens =
		chunk.token_count ?? Math.ceil(chunk.content.length / 4);
	return (
		<article className='chunk-record'>
			<header>
				<span className='element-sequence'>
					{chunk.position + 1}
				</span>
				<div>
					<strong>
						Chunk {chunk.position + 1}
					</strong>
					<small>
						{chunk.page_from
							? `Page ${chunk.page_from}${chunk.page_to && chunk.page_to !== chunk.page_from ? `–${chunk.page_to}` : ''}`
							: 'No page'}{' '}
						· {approximateTokens}{' '}
						{chunk.token_count == null
							? 'estimated '
							: ''}
						tokens · {chunk.content.length}{' '}
						characters
					</small>
				</div>
			</header>
			<p>{chunk.content}</p>
			<div className='chunk-elements'>
				<strong>
					Source elements (
					{chunk.element_ids.length})
				</strong>
				{chunk.element_ids.length > 0
					? chunk.element_ids.join(', ')
					: 'No element links were stored.'}
			</div>
			{Object.keys(chunk.metadata).length > 0 && (
				<div className='record-metadata'>
					<strong>Chunk metadata</strong>
					<pre>
						{JSON.stringify(
							chunk.metadata,
							null,
							2,
						)}
					</pre>
				</div>
			)}
		</article>
	);
}

export function ChatScreen({
	chat,
	projectChats,
	initialMessages,
	initialSources,
	initialPrompt,
	projectName,
}: ChatScreenProps) {
	const navigate = useSmoothNavigation();
	const [chats, setChats] = useState(projectChats);
	const [messages, setMessages] = useState(initialMessages);
	const [sources, setSources] = useState(initialSources);
	const [sending, setSending] = useState(false);
	const [uploading, setUploading] = useState(false);
	const [selectedUploadFile, setSelectedUploadFile] =
		useState<File | null>(null);
	const [sourcesOpen, setSourcesOpen] = useState(true);
	const [streamingId, setStreamingId] = useState<string | null>(null);
	const [copiedId, setCopiedId] = useState<string | null>(null);
	const [chatSidebarOpen, setChatSidebarOpen] = useState(true);
	const [menuChatId, setMenuChatId] = useState<string | null>(null);
	const [editingChatId, setEditingChatId] = useState<string | null>(null);
	const [deletingChatId, setDeletingChatId] = useState<string | null>(
		null,
	);
	const [chatActionBusy, setChatActionBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [inspection, setInspection] = useState<SourceInspection | null>(
		null,
	);
	const [inspectionLoading, setInspectionLoading] = useState<
		string | null
	>(null);
	const [inspectionTab, setInspectionTab] = useState<
		'elements' | 'chunks'
	>('elements');
	const [sourceToDelete, setSourceToDelete] = useState<Source | null>(
		null,
	);
	const [deletingSource, setDeletingSource] = useState(false);
	const fileRef = useRef<HTMLInputElement>(null);
	const composerRef = useRef<HTMLFormElement>(null);
	const initialPromptSentRef = useRef(false);
	const endRef = useRef<HTMLDivElement>(null);
	const abortRef = useRef<AbortController | null>(null);
	const hasActiveIngestion = sources.some(source =>
		activeStatuses.has(source.status),
	);

	useEffect(() => {
		endRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages, sending]);

	useEffect(() => {
		if (window.matchMedia('(max-width: 900px)').matches)
			setChatSidebarOpen(false);
	}, []);

	useEffect(() => {
		if (
			!initialPrompt ||
			initialMessages.length > 0 ||
			initialPromptSentRef.current ||
			hasActiveIngestion
		)
			return;
		initialPromptSentRef.current = true;
		composerRef.current?.requestSubmit();
	}, [hasActiveIngestion, initialMessages.length, initialPrompt]);

	useEffect(() => {
		if (!hasActiveIngestion) return;
		const timer = window.setInterval(async () => {
			try {
				const result = await json<{
					sources: Source[];
				}>(
					`/api/knowledge-bases/${chat.knowledge_base_id}/sources`,
				);
				setSources(result.sources);
			} catch {
				// Keep the existing state; the next poll can recover from a transient failure.
			}
		}, 4000);
		return () => window.clearInterval(timer);
	}, [chat.knowledge_base_id, hasActiveIngestion]);

	async function upload(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const uploadForm = event.currentTarget;
		const file = selectedUploadFile ?? fileRef.current?.files?.[0];
		if (!file) return;
		if (file.size > MAX_UPLOAD_BYTES) {
			setError('File size must not exceed 5 MB.');
			uploadForm.reset();
			setSelectedUploadFile(null);
			return;
		}
		setUploading(true);
		setError(null);
		try {
			const form = new FormData();
			form.set('file', file);
			const source = await json<Source>(
				`/api/knowledge-bases/${chat.knowledge_base_id}/sources`,
				{ method: 'POST', body: form },
			);
			setSources(current => [
				source,
				...current.filter(
					item => item.id !== source.id,
				),
			]);
			uploadForm.reset();
			setSelectedUploadFile(null);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Upload failed.',
			);
		} finally {
			setUploading(false);
		}
	}

	function chooseUploadFile(event: ChangeEvent<HTMLInputElement>) {
		const file = event.target.files?.[0] ?? null;
		if (file && file.size > MAX_UPLOAD_BYTES) {
			setError('File size must not exceed 5 MB.');
			event.target.value = '';
			setSelectedUploadFile(null);
			return;
		}
		setError(null);
		setSelectedUploadFile(file);
	}

	function clearSelectedUpload() {
		setSelectedUploadFile(null);
		if (fileRef.current) fileRef.current.value = '';
	}

	async function inspectSource(source: Source) {
		setInspectionLoading(source.id);
		setError(null);
		try {
			const result = await json<SourceInspection>(
				`/api/knowledge-bases/${chat.knowledge_base_id}/sources/${source.id}/inspection`,
			);
			setInspection(result);
			setInspectionTab('elements');
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not load the extraction details.',
			);
		} finally {
			setInspectionLoading(null);
		}
	}

	async function deleteSource() {
		if (!sourceToDelete || deletingSource) return;
		setDeletingSource(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/knowledge-bases/${chat.knowledge_base_id}/sources/${sourceToDelete.id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok) {
				const body = (await response
					.json()
					.catch(() => ({}))) as {
					error?: string | { message?: string };
				};
				throw new Error(
					typeof body.error === 'string'
						? body.error
						: (body.error?.message ??
								'Could not delete the source.'),
				);
			}
			setSources(current =>
				current.filter(
					source =>
						source.id !== sourceToDelete.id,
				),
			);
			if (inspection?.source_id === sourceToDelete.id)
				setInspection(null);
			setSourceToDelete(null);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not delete the source.',
			);
		} finally {
			setDeletingSource(false);
		}
	}

	async function send(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const form = new FormData(event.currentTarget);
		const content = String(form.get('content') ?? '').trim();
		if (!content || sending) return;
		const optimistic: Message = {
			id: `pending-${Date.now()}`,
			chat_id: chat.id,
			role: 'user',
			content,
			citations: [],
			created_at: new Date().toISOString(),
		};
		const assistantId = `streaming-${Date.now()}`;
		const assistantPlaceholder: Message = {
			id: assistantId,
			chat_id: chat.id,
			role: 'assistant',
			content: '',
			citations: [],
			created_at: new Date().toISOString(),
		};
		setMessages(current => [
			...current,
			optimistic,
			assistantPlaceholder,
		]);
		event.currentTarget.reset();
		setSending(true);
		setStreamingId(assistantId);
		setError(null);
		const controller = new AbortController();
		abortRef.current = controller;
		try {
			const response = await fetch(
				`/api/chats/${chat.id}/messages/stream`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({ content }),
					signal: controller.signal,
				},
			);
			if (response.status === 401) {
				window.location.assign(
					`/auth/signin?error=SessionExpired&callbackUrl=${encodeURIComponent(`/chats/${chat.id}`)}`,
				);
				return;
			}
			if (!response.ok || !response.body) {
				const body = (await response
					.json()
					.catch(() => ({}))) as {
					error?: string;
					detail?: string;
				};
				throw new Error(
					body.error ??
						body.detail ??
						'Could not start the response stream.',
				);
			}
			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			while (true) {
				const { value, done } = await reader.read();
				buffer += decoder.decode(value, {
					stream: !done,
				});
				const frames = buffer.split('\n\n');
				buffer = frames.pop() ?? '';
				for (const frame of frames) {
					const data = frame
						.split('\n')
						.find(line =>
							line.startsWith(
								'data:',
							),
						);
					if (!data) continue;
					const streamEvent = JSON.parse(
						data.slice(5).trim(),
					) as
						| {
								type: 'token';
								content: string;
						  }
						| {
								type: 'done';
								message: Message;
						  }
						| {
								type: 'error';
								message: string;
						  };
					if (streamEvent.type === 'token') {
						setMessages(current =>
							current.map(message =>
								message.id ===
								assistantId
									? {
											...message,
											content:
												message.content +
												streamEvent.content,
										}
									: message,
							),
						);
					} else if (
						streamEvent.type === 'done'
					) {
						setMessages(current =>
							current.map(message =>
								message.id ===
								assistantId
									? streamEvent.message
									: message,
							),
						);
					} else {
						throw new Error(
							streamEvent.message,
						);
					}
				}
				if (done) break;
			}
		} catch (caught) {
			if (
				caught instanceof DOMException &&
				caught.name === 'AbortError'
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
					caught instanceof Error
						? caught.message
						: 'Could not send message.',
				);
			}
		} finally {
			setSending(false);
			setStreamingId(null);
			abortRef.current = null;
		}
	}

	function composerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
		if (
			event.key === 'Enter' &&
			!event.shiftKey &&
			!event.nativeEvent.isComposing
		) {
			event.preventDefault();
			event.currentTarget.form?.requestSubmit();
		}
	}

	async function copyMessage(message: Message) {
		await navigator.clipboard.writeText(message.content);
		setCopiedId(message.id);
		window.setTimeout(() => setCopiedId(null), 1500);
	}

	function createChat() {
		navigate(`/?project=${chat.project_id}`);
	}

	async function renameChat(
		event: FormEvent<HTMLFormElement>,
		target: Chat,
	) {
		event.preventDefault();
		const title = String(
			new FormData(event.currentTarget).get('title') ?? '',
		).trim();
		if (!title) return;
		setChatActionBusy(true);
		try {
			const updated = await json<Chat>(
				`/api/chats/${target.id}`,
				{
					method: 'PATCH',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({ title }),
				},
			);
			setChats(current =>
				current.map(item =>
					item.id === updated.id ? updated : item,
				),
			);
			setEditingChatId(null);
			setMenuChatId(null);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not rename chat.',
			);
		} finally {
			setChatActionBusy(false);
		}
	}

	async function deleteChat(target: Chat) {
		setChatActionBusy(true);
		try {
			const response = await fetch(
				`/api/chats/${target.id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok)
				throw new Error('Could not delete chat.');
			const remaining = chats.filter(
				item => item.id !== target.id,
			);
			setChats(remaining);
			setDeletingChatId(null);
			if (target.id === chat.id)
				navigate(
					remaining[0]
						? `/chats/${remaining[0].id}`
						: '/',
				);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not delete chat.',
			);
		} finally {
			setChatActionBusy(false);
		}
	}

	return (
		<div
			className={`chat-app ${chatSidebarOpen ? '' : 'chat-sidebar-collapsed'}`}>
			<SessionSynchronizer />
			<aside className='chat-history-sidebar'>
				<div className='chat-sidebar-brand'>
					<SmoothLink
						href='/'
						aria-label='Projects'>
						<span className='editorial-brand-mark'>
							R
						</span>
						<strong>RagApp</strong>
					</SmoothLink>
					<button
						type='button'
						onClick={() =>
							setChatSidebarOpen(
								false,
							)
						}
						aria-label='Collapse chat sidebar'>
						<PanelLeftClose size={18} />
					</button>
				</div>
				<button
					className='new-chat-button'
					type='button'
					onClick={createChat}
					disabled={chatActionBusy}>
					<Plus size={17} />
					<span>New chat</span>
				</button>
				<div className='chat-project-block'>
					<div className='chat-history-label'>
						Project
					</div>
					<SmoothLink
						href={`/?project=${chat.project_id}`}>
						<Folder size={16} />
						<span>{projectName}</span>
					</SmoothLink>
				</div>
				<div className='chat-history-label'>
					Recent chats
				</div>
				<nav
					className='chat-history-list'
					aria-label='Chats'>
					{chats.map(item => (
						<div
							className={`history-chat-wrap ${item.id === chat.id ? 'active' : ''}`}
							key={item.id}>
							{editingChatId ===
							item.id ? (
								<form
									className='chat-rename-form'
									onSubmit={event =>
										renameChat(
											event,
											item,
										)
									}>
									<input
										name='title'
										defaultValue={
											item.title
										}
										maxLength={
											240
										}
										autoFocus
										onKeyDown={event => {
											if (
												event.key ===
												'Escape'
											)
												setEditingChatId(
													null,
												);
										}}
									/>
									<button
										type='submit'
										disabled={
											chatActionBusy
										}>
										<Check
											size={
												14
											}
										/>
									</button>
									<button
										type='button'
										onClick={() =>
											setEditingChatId(
												null,
											)
										}>
										<X
											size={
												14
											}
										/>
									</button>
								</form>
							) : (
								<>
									<SmoothLink
										href={`/chats/${item.id}`}>
										<MessageSquareText
											size={
												15
											}
										/>
										<span>
											{
												item.title
											}
										</span>
									</SmoothLink>
									<button
										className='chat-options-trigger'
										type='button'
										onClick={() =>
											setMenuChatId(
												current =>
													current ===
													item.id
														? null
														: item.id,
											)
										}
										aria-label={`Options for ${item.title}`}>
										<Ellipsis
											size={
												17
											}
										/>
									</button>
									{menuChatId ===
										item.id && (
										<div className='chat-options-menu'>
											<button
												type='button'
												onClick={() => {
													setEditingChatId(
														item.id,
													);
													setMenuChatId(
														null,
													);
												}}>
												<PencilLine
													size={
														14
													}
												/>{' '}
												Rename
											</button>
											<button
												className='danger'
												type='button'
												onClick={() => {
													setDeletingChatId(
														item.id,
													);
													setMenuChatId(
														null,
													);
												}}>
												<Trash
													size={
														14
													}
												/>{' '}
												Delete
											</button>
										</div>
									)}
								</>
							)}
							{deletingChatId ===
								item.id && (
								<div className='chat-delete-confirm'>
									<p>
										Delete
										this
										chat?
									</p>
									<span>
										This
										cannot
										be
										undone.
									</span>
									<div>
										<button
											type='button'
											onClick={() =>
												setDeletingChatId(
													null,
												)
											}>
											Cancel
										</button>
										<button
											className='danger'
											type='button'
											disabled={
												chatActionBusy
											}
											onClick={() =>
												deleteChat(
													item,
												)
											}>
											Delete
										</button>
									</div>
								</div>
							)}
						</div>
					))}
				</nav>
				<div className='chat-sidebar-footer'>
					<SmoothLink
						href='/'
						className='chat-sidebar-projects'>
						<ArrowLeft size={15} /> Back to
						projects
					</SmoothLink>
					<ThemeToggle />
				</div>
			</aside>
			{!chatSidebarOpen && (
				<button
					className='chat-sidebar-reopen'
					type='button'
					onClick={() => setChatSidebarOpen(true)}
					aria-label='Open chat sidebar'>
					<PanelLeftOpen size={19} />
				</button>
			)}
			<main className='chat-screen'>
				<header className='chat-page-header'>
					<button
						className='mobile-chat-menu'
						type='button'
						onClick={() =>
							setChatSidebarOpen(true)
						}
						aria-label='Open chats'>
						<Menu size={18} />
					</button>
					<div className='editorial-chat-title'>
						<div
							className='chat-title-breadcrumb'
							aria-label='Project and chat'>
							<SmoothLink
								href={`/?project=${chat.project_id}`}>
								{projectName}
							</SmoothLink>
							<ChevronRight
								size={20}
								aria-hidden='true'
							/>
							<h1>{chat.title}</h1>
						</div>
						<p>
							Ask your documents. Get
							source-backed answers.
						</p>
					</div>
					<button
						type='button'
						className='header-sources-toggle'
						onClick={() =>
							setSourcesOpen(
								open => !open,
							)
						}>
						{sourcesOpen
							? 'Hide sources'
							: 'Show sources'}
						<PanelRightOpen size={15} />
					</button>
				</header>
				{error && (
					<div
						className='workspace-error'
						role='alert'>
						<span>{error}</span>
						<button
							onClick={() =>
								setError(null)
							}>
							<CircleAlert
								size={16}
							/>
						</button>
					</div>
				)}
				<div
					className={`chat-layout ${sourcesOpen ? '' : 'sources-collapsed'}`}>
					<section className='conversation-panel panel'>
						<div className='conversation-messages'>
							{messages.length ===
								0 && (
								<div className='conversation-empty'>
									<div className='empty-icon'>
										<MessageSquareText
											size={
												28
											}
										/>
									</div>
									<h2>
										Ask
										about
										your
										sources
									</h2>
									<p>
										Upload
										a
										document,
										wait
										until
										it
										is
										ready,
										then
										ask
										a
										focused
										question.
									</p>
								</div>
							)}
							{messages.map(
								message => (
									<article
										className={`message-row ${message.role}`}
										key={
											message.id
										}>
										<div className='message-avatar'>
											{message.role ===
											'assistant' ? (
												'AI'
											) : (
												<User
													size={
														17
													}
												/>
											)}
										</div>
										<div className='message-body'>
											<div className='message-meta'>
												<strong>
													{message.role ===
													'assistant'
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
											{message.role ===
											'assistant' ? (
												<div className='message-markdown'>
													<ReactMarkdown
														remarkPlugins={[
															remarkGfm,
														]}
														components={{
															a: ({
																children,
																...chatScreenProps
															}) => (
																<a
																	{...chatScreenProps}
																	target='_blank'
																	rel='noreferrer'>
																	{
																		children
																	}
																</a>
															),
														}}>
														{
															message.content
														}
													</ReactMarkdown>
													{message.id ===
														streamingId && (
														<span
															className='streaming-cursor'
															aria-label='Generating'
														/>
													)}
												</div>
											) : (
												<p>
													{
														message.content
													}
												</p>
											)}
											{message
												.citations
												.length >
												0 && (
												<details className='citation-group'>
													<summary>
														<Files
															size={
																14
															}
														/>{' '}
														Sources{' '}
														<span>
															{
																message
																	.citations
																	.length
															}
														</span>
														<ChevronDown
															size={
																14
															}
															className='citation-chevron'
														/>
													</summary>
													<div className='citation-list'>
														{message.citations.map(
															(
																citation,
																index,
															) => (
																<article
																	key={`${citation.chunk_id}-${index}`}>
																	<strong>
																		[
																		{index +
																			1}

																		]{' '}
																		{
																			citation.source_filename
																		}
																		{citation.page_number
																			? ` · page ${citation.page_number}`
																			: ''}
																	</strong>
																	<blockquote>
																		{
																			citation.excerpt
																		}
																	</blockquote>
																</article>
															),
														)}
													</div>
												</details>
											)}
											{message.role ===
												'assistant' &&
												message.id !==
													streamingId && (
													<div className='message-actions'>
														<button
															type='button'
															onClick={() =>
																copyMessage(
																	message,
																)
															}
															aria-label='Copy response'>
															{copiedId ===
															message.id ? (
																<Check
																	size={
																		14
																	}
																/>
															) : (
																<Copy
																	size={
																		14
																	}
																/>
															)}
															{copiedId ===
															message.id
																? 'Copied'
																: 'Copy'}
														</button>
													</div>
												)}
										</div>
									</article>
								),
							)}
							<div ref={endRef} />
						</div>
						<form
							ref={composerRef}
							className='message-composer'
							onSubmit={send}>
							<textarea
								name='content'
								rows={2}
								maxLength={
									12000
								}
								required
								disabled={
									sending
								}
								defaultValue={
									initialMessages.length ===
									0
										? initialPrompt
										: undefined
								}
								onKeyDown={
									composerKeyDown
								}
								placeholder={
									sources.some(
										source =>
											source.status ===
											'ready',
									)
										? 'Message RagApp…'
										: 'Upload a source or ask a question…'
								}
							/>
							{sending ? (
								<button
									type='button'
									onClick={() =>
										abortRef.current?.abort()
									}
									aria-label='Stop generating'>
									<Square
										size={
											15
										}
										fill='currentColor'
									/>
								</button>
							) : (
								<button
									type='submit'
									aria-label='Send message'>
									<ArrowUp
										size={
											20
										}
									/>
								</button>
							)}
							<small className='composer-hint'>
								Enter to send ·
								Shift + Enter
								for a new line
							</small>
						</form>
					</section>
					<aside className='sources-panel panel'>
						<div className='sources-heading'>
							<div className='sources-title'>
								<h2>Sources</h2>
							</div>
							<span>
								{sources.length}
							</span>
						</div>
						{sourcesOpen && (
							<>
								<form
									className='source-upload'
									onSubmit={
										upload
									}>
									<input
										ref={
											fileRef
										}
										id='source-file'
										name='file'
										type='file'
										required
										onChange={
											chooseUploadFile
										}
									/>
									<div className='source-file-picker'>
										<label
											className={
												selectedUploadFile
													? 'file-selected'
													: ''
											}
											htmlFor='source-file'>
											<Upload
												size={
													20
												}
											/>
											<span>
												<strong>
													{selectedUploadFile
														? selectedUploadFile.name
														: 'Add a source'}
												</strong>
												<small>
													{selectedUploadFile
														? `${formatBytes(selectedUploadFile.size)} · Ready to upload`
														: 'PDF, DOCX, text, and more · max 5 MB'}
												</small>
											</span>
										</label>
										{selectedUploadFile && (
											<button
												type='button'
												className='selected-file-action'
												onClick={
													clearSelectedUpload
												}
												aria-label={`Remove ${selectedUploadFile.name}`}>
												<CircleCheck
													className='file-check-icon'
													size={
														18
													}
												/>
												<X
													className='file-remove-icon'
													size={
														18
													}
												/>
											</button>
										)}
									</div>
									<button
										className='primary-action full'
										disabled={
											uploading ||
											!selectedUploadFile
										}>
										{uploading ? (
											<LoaderCircle
												className='spin'
												size={
													17
												}
											/>
										) : (
											<Paperclip
												size={
													17
												}
											/>
										)}{' '}
										{uploading
											? 'Uploading…'
											: 'Upload'}
									</button>
								</form>
								<div className='source-list'>
									{sources.map(
										source => (
											<article
												className='source-item'
												key={
													source.id
												}>
												<button
													type='button'
													className='source-open-button'
													onClick={() =>
														inspectSource(
															source,
														)
													}
													disabled={
														inspectionLoading ===
														source.id
													}>
													<div className='source-file-icon'>
														<FileText
															size={
																18
															}
														/>
													</div>
													<div>
														<strong
															title={
																source.display_name
															}>
															{
																source.display_name
															}
														</strong>
														<small>
															{formatBytes(
																source.byte_size,
															)}{' '}
															·
															v
															{
																source.version
															}
														</small>
														<span
															className={`source-status ${source.status}`}>
															{source.status ===
															'ready' ? (
																<CircleCheck
																	size={
																		12
																	}
																/>
															) : activeStatuses.has(
																	source.status,
															  ) ? (
																<LoaderCircle
																	className='spin'
																	size={
																		12
																	}
																/>
															) : (
																<CircleAlert
																	size={
																		12
																	}
																/>
															)}
															{
																source.status
															}
														</span>
													</div>
													<span className='source-inspect-icon'>
														{inspectionLoading ===
														source.id ? (
															<LoaderCircle
																className='spin'
																size={
																	15
																}
															/>
														) : (
															<ScanEye
																size={
																	15
																}
															/>
														)}
													</span>
												</button>
												<button
													type='button'
													className='source-delete-button'
													onClick={() =>
														setSourceToDelete(
															source,
														)
													}
													aria-label={`Delete ${source.display_name}`}>
													<Trash
														size={
															15
														}
													/>
												</button>
											</article>
										),
									)}
									{sources.length ===
										0 && (
										<div className='sources-empty'>
											<Files
												size={
													22
												}
											/>
											<p>
												No
												sources
												uploaded
												yet.
											</p>
										</div>
									)}
								</div>
							</>
						)}
					</aside>
				</div>
				{sourceToDelete && (
					<div
						className='modal-backdrop'
						role='dialog'
						aria-modal='true'
						aria-labelledby='delete-source-title'>
						<section className='workspace-modal delete-source-modal'>
							<div className='modal-title'>
								<div>
									<span className='eyebrow'>
										Remove
										source
									</span>
									<h2 id='delete-source-title'>
										Delete
										this
										source?
									</h2>
								</div>
								<button
									type='button'
									className='icon-action'
									onClick={() =>
										setSourceToDelete(
											null,
										)
									}
									aria-label='Close'>
									<X
										size={
											18
										}
									/>
								</button>
							</div>
							<p className='modal-copy'>
								<strong>
									{
										sourceToDelete.display_name
									}
								</strong>{' '}
								and its OCR
								elements,
								chunks,
								embeddings, and
								stored file will
								be permanently
								deleted.
							</p>
							<div className='delete-source-actions'>
								<button
									type='button'
									onClick={() =>
										setSourceToDelete(
											null,
										)
									}
									disabled={
										deletingSource
									}>
									Cancel
								</button>
								<button
									type='button'
									className='danger-action'
									onClick={
										deleteSource
									}
									disabled={
										deletingSource
									}>
									{deletingSource ? (
										<LoaderCircle
											className='spin'
											size={
												16
											}
										/>
									) : (
										<Trash
											size={
												16
											}
										/>
									)}{' '}
									Delete
									source
								</button>
							</div>
						</section>
					</div>
				)}
				{inspection && (
					<div
						className='inspection-backdrop'
						role='dialog'
						aria-modal='true'
						aria-labelledby='inspection-title'
						onMouseDown={event => {
							if (
								event.target ===
								event.currentTarget
							)
								setInspection(
									null,
								);
						}}>
						<section className='inspection-drawer'>
							<header>
								<div>
									<span className='eyebrow'>
										OCR
										inspection
									</span>
									<h2 id='inspection-title'>
										{
											inspection.filename
										}
									</h2>
								</div>
								<button
									type='button'
									className='icon-action'
									onClick={() =>
										setInspection(
											null,
										)
									}
									aria-label='Close extraction inspection'>
									<X
										size={
											19
										}
									/>
								</button>
							</header>
							<div className='inspection-summary'>
								<span>
									<strong>
										{
											inspection.element_count
										}
									</strong>{' '}
									elements
								</span>
								<span>
									<strong>
										{
											inspection.chunk_count
										}
									</strong>{' '}
									chunks
								</span>
								<span>
									<strong>
										{inspection.parser_name ||
											'Unknown'}
									</strong>{' '}
									parser
									{inspection.parser_version
										? ` · ${inspection.parser_version}`
										: ''}
								</span>
							</div>
							{inspection.error_message && (
								<div className='workspace-error'>
									<span>
										{
											inspection.error_message
										}
									</span>
								</div>
							)}
							<div
								className='inspection-tabs'
								role='tablist'>
								<button
									type='button'
									role='tab'
									aria-selected={
										inspectionTab ===
										'elements'
									}
									className={
										inspectionTab ===
										'elements'
											? 'active'
											: ''
									}
									onClick={() =>
										setInspectionTab(
											'elements',
										)
									}>
									OCR
									elements
								</button>
								<button
									type='button'
									role='tab'
									aria-selected={
										inspectionTab ===
										'chunks'
									}
									className={
										inspectionTab ===
										'chunks'
											? 'active'
											: ''
									}
									onClick={() =>
										setInspectionTab(
											'chunks',
										)
									}>
									RAG
									chunks
								</button>
							</div>
							<div className='inspection-content'>
								{inspectionTab ===
								'elements' ? (
									<>
										{inspection.elements.map(
											element => (
												<OcrElementCard
													element={
														element
													}
													key={
														element.element_id
													}
												/>
											),
										)}
										{inspection
											.elements
											.length ===
											0 && (
											<div className='inspection-empty'>
												No
												OCR
												elements
												have
												been
												stored
												for
												this
												source.
											</div>
										)}
									</>
								) : (
									<>
										{inspection.chunks.map(
											chunk => (
												<RagChunkCard
													chunk={
														chunk
													}
													key={
														chunk.id
													}
												/>
											),
										)}
										{inspection
											.chunks
											.length ===
											0 && (
											<div className='inspection-empty'>
												No
												RAG
												chunks
												have
												been
												generated
												for
												this
												source
												yet.
											</div>
										)}
									</>
								)}
							</div>
						</section>
					</div>
				)}
				{inspection && (
					<div
						className='inspection-version-pill'
						aria-label={`Inspecting version ${inspection.version}`}>
						Version {inspection.version}
					</div>
				)}
			</main>
		</div>
	);
}
