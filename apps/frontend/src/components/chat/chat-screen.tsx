'use client';

import {
	ChangeEvent,
	FormEvent,
	useEffect,
	useRef,
	useState,
} from 'react';
import {
	CircleAlert,
	LoaderCircle,
	Trash,
	X,
} from 'lucide-react';
import type {
	Chat,
	Message,
	Source,
	SourceInspection,
} from '@/types/workspace';
import { SessionSynchronizer } from '@/components/auth/session-synchronizer';
import { useSessionExpired } from '@/components/auth/session-expired-provider';
import { useSmoothNavigation } from '@/components/navigation/smooth-link';
import { ChatScreenProps } from '@/types/chat-screen';
import { ChatSidebar } from './chat-sidebar';
import { ChatHeader } from './chat-header';
import { MessageList } from './message-list';
import { MessageComposer } from './message-composer';
import { SourcesPanel } from './sources-panel';

async function json<T>(
	url: string,
	init?: RequestInit,
): Promise<T> {
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

const activeStatuses = new Set([
	'uploaded',
	'queued',
	'processing',
]);
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export function ChatScreen({
	chat,
	projectChats,
	initialMessages,
	initialSources,
	initialPrompt,
	projectName,
}: ChatScreenProps) {
	const navigate = useSmoothNavigation();
	const { showSessionExpired } = useSessionExpired();
	const [chats, setChats] = useState(projectChats);
	const [messages, setMessages] =
		useState(initialMessages);
	const [sources, setSources] =
		useState(initialSources);
	const [sending, setSending] = useState(false);
	const [uploading, setUploading] = useState(false);
	const [selectedUploadFiles, setSelectedUploadFiles] =
		useState<File[]>([]);
	const [sourcesOpen, setSourcesOpen] = useState(false);
	const [streamingId, setStreamingId] = useState<
		string | null
	>(null);
	const [copiedId, setCopiedId] = useState<
		string | null
	>(null);
	const [chatSidebarOpen, setChatSidebarOpen] =
		useState(true);
	const [menuChatId, setMenuChatId] = useState<
		string | null
	>(null);
	const [editingChatId, setEditingChatId] = useState<
		string | null
	>(null);
	const [deletingChatId, setDeletingChatId] = useState<
		string | null
	>(null);
	const [chatActionBusy, setChatActionBusy] =
		useState(false);
	const [error, setError] = useState<string | null>(
		null,
	);
	const [inspection, setInspection] =
		useState<SourceInspection | null>(null);
	const [, setInspectionLoading] =
		useState<string | null>(null);
	const [sourceToDelete, setSourceToDelete] =
		useState<Source | null>(null);
	const [deletingSource, setDeletingSource] =
		useState(false);
	const fileRef = useRef<HTMLInputElement>(null);
	const composerRef = useRef<HTMLFormElement>(null);
	const initialPromptSentRef = useRef(false);
	const endRef = useRef<HTMLDivElement>(null);
	const abortRef = useRef<AbortController | null>(null);
	const hasActiveIngestion = sources.some(source =>
		activeStatuses.has(source.status),
	);

	useEffect(() => {
		endRef.current?.scrollIntoView({
			behavior: 'smooth',
		});
	}, [messages, sending]);

	useEffect(() => {
		if (
			window.matchMedia('(max-width: 900px)')
				.matches
		)
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
	}, [
		hasActiveIngestion,
		initialMessages.length,
		initialPrompt,
	]);

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
			} catch {}
		}, 4000);
		return () => window.clearInterval(timer);
	}, [
		chat.knowledge_base_id,
		hasActiveIngestion,
	]);

	useEffect(() => {
		function handleKeyDown(event: KeyboardEvent) {
			if (
				event.key === 'Escape' &&
				sourcesOpen
			) {
				setSourcesOpen(false);
			}
		}
		document.addEventListener(
			'keydown',
			handleKeyDown,
		);
		return () =>
			document.removeEventListener(
				'keydown',
				handleKeyDown,
			);
	}, [sourcesOpen]);

	async function upload(
		event: FormEvent<HTMLFormElement>,
	) {
		event.preventDefault();
		const uploadForm = event.currentTarget;
		const files =
			selectedUploadFiles.length > 0
				? selectedUploadFiles
				: fileRef.current?.files
					? Array.from(fileRef.current.files)
					: [];
		if (files.length === 0) return;
		const oversized = files.find(
			f => f.size > MAX_UPLOAD_BYTES,
		);
		if (oversized) {
			setError(
				`"${oversized.name}" exceeds 10 MB limit.`,
			);
			uploadForm.reset();
			setSelectedUploadFiles([]);
			return;
		}
		setUploading(true);
		setError(null);
		try {
			for (const file of files) {
				const form = new FormData();
				form.set('file', file);
				const source = await json<Source>(
					`/api/knowledge-bases/${chat.knowledge_base_id}/sources`,
					{
						method: 'POST',
						body: form,
					},
				);
				setSources(current => [
					source,
					...current.filter(
						item => item.id !== source.id,
					),
				]);
			}
			uploadForm.reset();
			setSelectedUploadFiles([]);
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

	function chooseUploadFiles(
		event: ChangeEvent<HTMLInputElement>,
	) {
		const incoming = Array.from(
			event.target.files ?? [],
		);
		const combined = [
			...selectedUploadFiles,
			...incoming,
		].slice(0, 5);
		const oversized = combined.find(
			f => f.size > MAX_UPLOAD_BYTES,
		);
		if (oversized) {
			setError(
				`"${oversized.name}" exceeds 10 MB limit.`,
			);
			event.target.value = '';
			return;
		}
		setError(null);
		setSelectedUploadFiles(combined);
		event.target.value = '';
	}

	function removeSelectedFile(index: number) {
		setSelectedUploadFiles(current =>
			current.filter((_, i) => i !== index),
		);
	}

	function clearSelectedUpload() {
		setSelectedUploadFiles([]);
		if (fileRef.current)
			fileRef.current.value = '';
	}

	async function inspectSource(source: Source) {
		setInspectionLoading(source.id);
		setError(null);
		try {
			const result =
				await json<SourceInspection>(
					`/api/knowledge-bases/${chat.knowledge_base_id}/sources/${source.id}/inspection`,
				);
			setInspection(result);
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
		if (!sourceToDelete || deletingSource)
			return;
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
					error?: string | {
						message?: string;
					};
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
						source.id !==
						sourceToDelete.id,
				),
			);
			if (
				inspection?.source_id ===
				sourceToDelete.id
			)
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

	async function sendContent(content: string) {
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
				showSessionExpired();
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
			const reader =
				response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			while (true) {
				const { value, done } =
					await reader.read();
				buffer += decoder.decode(value, {
					stream: !done,
				});
				const frames =
					buffer.split('\n\n');
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
					if (
						streamEvent.type === 'token'
					) {
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
						message.id ===
							assistantId &&
						!message.content
							? {
									...message,
									content:
										'_Response stopped._',
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

	async function send(
		event: FormEvent<HTMLFormElement>,
	) {
		event.preventDefault();
		const form = event.currentTarget;
		if (!form) return;
		const content = String(
			new FormData(form).get('content') ?? '',
		).trim();
		form.reset();
		await sendContent(content);
	}

	function copyMessage(message: Message) {
		navigator.clipboard.writeText(
			message.content,
		);
		setCopiedId(message.id);
		window.setTimeout(
			() => setCopiedId(null),
			1500,
		);
	}

	function createChat() {
		navigate(
			`/?project=${chat.project_id}`,
		);
	}

	async function renameChat(
		event: FormEvent<HTMLFormElement>,
		target: Chat,
	) {
		event.preventDefault();
		const title = String(
			new FormData(event.currentTarget).get(
				'title',
			) ?? '',
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
					item.id === updated.id
						? updated
						: item,
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
				throw new Error(
					'Could not delete chat.',
				);
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
			<ChatSidebar
				chat={chat}
				chats={chats}
				projectName={projectName}
				chatSidebarOpen={chatSidebarOpen}
				setChatSidebarOpen={
					setChatSidebarOpen
				}
				menuChatId={menuChatId}
				setMenuChatId={setMenuChatId}
				editingChatId={editingChatId}
				setEditingChatId={
					setEditingChatId
				}
				deletingChatId={deletingChatId}
				setDeletingChatId={
					setDeletingChatId
				}
				chatActionBusy={chatActionBusy}
				onRename={renameChat}
				onDelete={deleteChat}
				onCreateChat={createChat}
			/>
			<main className='chat-screen'>
				<ChatHeader
					title={chat.title}
					sourcesOpen={sourcesOpen}
					sourcesCount={sources.length}
					onToggleSources={() =>
						setSourcesOpen(
							open => !open,
						)
					}
					onOpenSidebar={() =>
						setChatSidebarOpen(true)
					}
				/>
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
				<div className='chat-column'>
					<MessageList
						messages={messages}
						streamingId={streamingId}
						copiedId={copiedId}
						onCopy={copyMessage}
						onSuggest={sendContent}
						endRef={endRef}
					/>
					<MessageComposer
						ref={composerRef}
						sending={sending}
						placeholder={
							sources.some(
								source =>
									source.status ===
									'ready',
							)
								? 'Message kayceejenz.ai...'
								: 'Upload a source or ask a question…'
						}
						defaultValue={
							initialMessages.length ===
							0
								? initialPrompt
								: undefined
						}
						onSubmit={send}
						onStop={() =>
							abortRef.current?.abort()
						}
					/>
				</div>
				<div
					className={`sources-drawer ${sourcesOpen ? 'open' : ''}`}>
					<div
						className='sources-drawer-backdrop'
						onClick={() =>
							setSourcesOpen(false)
						}
					/>
					<div className='sources-drawer-panel'>
						<div className='sources-drawer-header'>
							<h2>Sources</h2>
							<button
								type='button'
								onClick={() =>
									setSourcesOpen(
										false,
									)
								}
								aria-label='Close sources'>
								<X size={18} />
							</button>
						</div>
						<SourcesPanel
							sources={sources}
							selectedUploadFiles={
								selectedUploadFiles
							}
							uploading={uploading}
							onChooseFiles={
								chooseUploadFiles
							}
							onRemoveFile={
								removeSelectedFile
							}
							onClearSelected={
								clearSelectedUpload
							}
							onUpload={upload}
						onInspect={
							inspectSource
						}
						setSourceToDelete={
								setSourceToDelete
							}
						/>
					</div>
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
										Source
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
									aria-label='Close source inspection'>
									<X
										size={
											19
										}
									/>
								</button>
							</header>
							<div className='inspection-summary'>
								<span>
									Version{' '}
									<strong>
										{
											inspection.version
										}
									</strong>
								</span>
								<span>
									Status{' '}
									<strong>
										{
											inspection.status
										}
									</strong>
								</span>
							</div>
							<div className='inspection-content'>
								<a
									className='primary-action'
									href={`/api/knowledge-bases/${chat.knowledge_base_id}/sources/${inspection.source_id}/file`}
									target='_blank'
									rel='noopener noreferrer'>
									Open file
								</a>
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
