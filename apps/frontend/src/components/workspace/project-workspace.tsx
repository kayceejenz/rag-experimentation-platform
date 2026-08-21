'use client';

import { useSmoothNavigation } from '@/components/navigation/smooth-link';
import type { Chat, Project } from '@/types/workspace';
import {
	ArrowUp,
	ChevronDown,
	FileText,
	Folder,
	LoaderCircle,
	Paperclip,
	Plus,
	X,
} from 'lucide-react';
import { ChangeEvent, FormEvent, KeyboardEvent, useRef, useState } from 'react';

type Props = {
	initialProjects: Project[];
	initialSelectedId?: string | null;
	initialShowProjectForm?: boolean;
};

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
	const response = await fetch(url, init);
	const body = (await response.json().catch(() => ({}))) as T & {
		error?: string | { message?: string };
		detail?: string | { message?: string };
	};
	if (!response.ok) {
		const error =
			typeof body.error === 'string'
				? body.error
				: body.error?.message;
		const detail =
			typeof body.detail === 'string'
				? body.detail
				: body.detail?.message;
		throw new Error(error ?? detail ?? 'The request failed.');
	}
	return body;
}
export function ProjectWorkspace({
	initialProjects,
	initialSelectedId,
	initialShowProjectForm = false,
}: Props) {
	const navigate = useSmoothNavigation();
	const sourceInputRef = useRef<HTMLInputElement>(null);
	const [projects, setProjects] = useState(initialProjects);
	const [selectedId, setSelectedId] = useState(
		initialSelectedId ?? initialProjects[0]?.id ?? null,
	);
	const [showProjectForm, setShowProjectForm] = useState(
		initialShowProjectForm,
	);
	const [message, setMessage] = useState('');
	const [sourceFiles, setSourceFiles] = useState<File[]>([]);
	const [busy, setBusy] = useState<'project' | 'chat' | null>(null);
	const [error, setError] = useState<string | null>(null);

	async function createProject(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const form = new FormData(event.currentTarget);
		setBusy('project');
		setError(null);
		try {
			const project = await requestJson<Project>(
				'/api/projects',
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						name: form.get('name'),
						description:
							form.get(
								'description',
							) || null,
					}),
				},
			);
			setProjects(current => [project, ...current]);
			setSelectedId(project.id);
			setShowProjectForm(false);
			navigate(`/?project=${project.id}`);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not create project.',
			);
		} finally {
			setBusy(null);
		}
	}

	async function startChat(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const content = message.trim();
		if (!content || !selectedId || busy === 'chat') return;
		setBusy('chat');
		setError(null);
		try {
			const title =
				content.length > 70
					? `${content.slice(0, 67)}…`
					: content;
			const chat = await requestJson<Chat>(
				`/api/projects/${selectedId}/chats`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({ title }),
				},
			);
			if (sourceFiles.length > 0) {
				for (const file of sourceFiles) {
					const form = new FormData();
					form.set('file', file);
					await requestJson(
						`/api/knowledge-bases/${chat.knowledge_base_id}/sources`,
						{ method: 'POST', body: form },
					);
				}
			}
			navigate(
				`/chats/${chat.id}?prompt=${encodeURIComponent(content)}`,
			);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not start the chat.',
			);
			setBusy(null);
		}
	}

	function selectSource(event: ChangeEvent<HTMLInputElement>) {
		const incoming = Array.from(event.target.files ?? []);
		const combined = [...sourceFiles, ...incoming].slice(0, 5);
		const oversized = combined.find(f => f.size > 10 * 1024 * 1024);
		if (oversized) {
			setError(`"${oversized.name}" exceeds 10 MB limit.`);
			event.target.value = '';
			return;
		}
		setError(null);
		setSourceFiles(combined);
		event.target.value = '';
	}

	function removeSourceFile(index: number) {
		setSourceFiles(current => current.filter((_, i) => i !== index));
	}

	function chooseProject(value: string) {
		if (value === '__new__') return setShowProjectForm(true);
		setSelectedId(value);
		setError(null);
	}

	function closeProjectForm() {
		setShowProjectForm(false);
		if (initialShowProjectForm)
			navigate(selectedId ? `/?project=${selectedId}` : '/');
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

	return (
		<div className='home-chat-layout'>
			<section className='project-main'>
				{error && (
					<div
						className='workspace-error'
						role='alert'>
						<span>{error}</span>
						<button
							onClick={() =>
								setError(null)
							}
							aria-label='Dismiss error'>
							<X size={16} />
						</button>
					</div>
				)}
				<section className='ai-launchpad'>
					<h1>What can I help you explore?</h1>
					<div className='ai-starter-grid'>
						{/* <button
							type='button'
							onClick={() =>
								setMessage(
									'What are the most important insights in my knowledge base?',
								)
							}>
							<span className='starter-icon'>
								<Search
									size={
										17
									}
								/>
							</span>
							<span>
								<strong>
									Ask your
									knowledge
								</strong>
								<small>
									Get
									source-backed
									answers
								</small>
							</span>
							<Plus size={15} />
						</button>
						<button type='button' disabled>
							<span className='starter-icon'>
								<FileText
									size={
										17
									}
								/>
							</span>
							<span>
								<strong>
									Summarize
									documents
								</strong>
								<small>
									Extract
									the
									important
									details
								</small>
							</span>
							<span className='coming-soon'>
								Coming soon
							</span>
						</button>
						<button type='button' disabled>
							<span className='starter-icon'>
								<Globe
									size={
										17
									}
								/>
							</span>
							<span>
								<strong>
									Research
									a topic
								</strong>
								<small>
									Explore
									connected
									sources
								</small>
							</span>
							<span className='coming-soon'>
								Coming soon
							</span>
						</button>
						<button type='button' disabled>
							<span className='starter-icon'>
								<BetweenHorizontalEnd
									size={
										17
									}
								/>
							</span>
							<span>
								<strong>
									Compare
									sources
								</strong>
								<small>
									Find
									agreements
									and
									differences
								</small>
							</span>
							<span className='coming-soon'>
								Coming soon
							</span>
						</button> */}
					</div>
					<form
						className='ai-start-composer'
						onSubmit={startChat}>
						<input
							ref={
								sourceInputRef
							}
							id='new-chat-source'
							className='composer-source-input'
							type='file'
							multiple
							accept='.pdf,.doc,.docx,.txt,.csv,.md,.json,.xlsx,.xls'
							onChange={
								selectSource
							}
						/>
						{sourceFiles.length > 0 && (
							<div className='composer-attachments'>
								{sourceFiles.map(
									(file, i) => (
										<span
											key={`${file.name}-${i}`}
											className='attachment-chip'>
											<FileText size={12} />
											<span className='attachment-chip-name'>
												{file.name}
											</span>
											<button
												type='button'
												className='attachment-chip-remove'
												onClick={() =>
													removeSourceFile(
														i,
													)
												}
												aria-label={`Remove ${file.name}`}>
												<X size={11} />
											</button>
										</span>
									),
								)}
							</div>
						)}
						<textarea
							value={message}
							onChange={event =>
								setMessage(
									event
										.target
										.value,
								)
							}
							onKeyDown={
								composerKeyDown
							}
							rows={2}
							maxLength={12000}
							required
							placeholder='Ask for insight…'
							aria-label='Message'
						/>
						<div className='composer-tools'>
							<div className='composer-tools-left'>
								{sourceFiles.length < 5 && (
									<label
										className='composer-source-button'
										htmlFor='new-chat-source'>
										<Paperclip size={14} />
										<span>
											{sourceFiles.length === 0
												? 'Add sources'
												: `Add more (${sourceFiles.length}/5)`}
										</span>
									</label>
								)}
							</div>
							<div className='composer-project-control'>
								<Folder
									size={
										13
									}
								/>
								<select
									value={
										selectedId ??
										''
									}
									onChange={event =>
										chooseProject(
											event
												.target
												.value,
										)
									}
									required
									aria-label='Attach project'>
									<option
										value=''
										disabled>
										Attach
										a
										project
									</option>
									{projects.map(
										project => (
											<option
												key={
													project.id
												}
												value={
													project.id
												}>
												{
													project.name
												}
											</option>
										),
									)}
									<option value='__new__'>
										＋
										Create
										new
										project
									</option>
								</select>
								<ChevronDown
									size={
										12
									}
								/>
							</div>
							<button
								type='submit'
								disabled={
									busy ===
										'chat' ||
									!selectedId ||
									!message.trim()
								}
								aria-label='Send message'>
								{busy ===
								'chat' ? (
									<LoaderCircle
										className='spin'
										size={
											16
										}
									/>
								) : (
									<ArrowUp
										size={
											18
										}
									/>
								)}
							</button>
						</div>
					</form>
					<small className='ai-disclaimer'>
						kayceejenz.ai can make mistakes. Check
						important answers against their
						sources.
					</small>
				</section>
			</section>

			{showProjectForm && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'
					aria-labelledby='create-project-title'
					onMouseDown={event => {
						if (
							event.target ===
							event.currentTarget
						)
							closeProjectForm();
					}}>
					<form
						className='workspace-modal create-project-modal'
						onSubmit={createProject}>
						<div className='modal-title'>
							<div>
								<h2 id='create-project-title'>
									Create
									project
								</h2>
								<p>
									Organize
									related
									chats
									and
									sources
									in one
									place.
								</p>
							</div>
							<button
								type='button'
								className='icon-action'
								onClick={
									closeProjectForm
								}
								aria-label='Close create project dialog'>
								<X size={18} />
							</button>
						</div>
						<div className='project-form-fields'>
							<label>
								Project name
								<input
									name='name'
									required
									minLength={
										2
									}
									maxLength={
										120
									}
									autoFocus
									autoComplete='off'
									placeholder='e.g. Customer support'
								/>
							</label>
							<label>
								Description{' '}
								<small>
									Optional
								</small>
								<textarea
									name='description'
									maxLength={
										500
									}
									rows={4}
									placeholder='What will this project help you accomplish?'
								/>
							</label>
						</div>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={
									closeProjectForm
								}>
								Cancel
							</button>
							<button
								className='primary-action'
								disabled={
									busy ===
									'project'
								}>
								{busy ===
								'project' ? (
									<LoaderCircle
										className='spin'
										size={
											17
										}
									/>
								) : (
									<Plus
										size={
											17
										}
									/>
								)}{' '}
								Create project
							</button>
						</div>
					</form>
				</div>
			)}
		</div>
	);
}
