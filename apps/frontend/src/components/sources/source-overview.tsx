'use client';

import { DragEvent, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import {
	Activity,
	ChevronRight,
	Eye,
	FileText,
	Folder,
	FolderPlus,
	Trash2,
	Upload,
	X,
} from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type {
	KnowledgeActivityEvent,
	KnowledgeBase,
	KnowledgeFolder,
	Project,
	Source,
} from '@/types/workspace';

const sourceSections = [
	{
		key: 'documents',
		title: 'Documents',
		description:
			'Files and external content registered in this knowledge source.',
		icon: FileText,
	},
	{
		key: 'activity',
		title: 'Activity',
		description:
			'Review recent document uploads and knowledge processing events.',
		icon: Activity,
	},
];

type Props = {
	project: Project;
	source: KnowledgeBase;
	initialDocuments: Source[];
	initialActivity: KnowledgeActivityEvent[];
	initialFolders: KnowledgeFolder[];
	active?: string;
};

async function json<T>(url: string, init?: RequestInit): Promise<T> {
	const response = await fetch(url, init);
	const body = await response.json().catch(() => ({}));
	if (!response.ok)
		throw new Error(
			body?.error?.message ??
				body?.detail ??
				'Request failed',
		);
	return body as T;
}

export function SourceOverview({
	project,
	source,
	initialDocuments,
	initialActivity,
	initialFolders,
	active,
}: Props) {
	const base = `/projects/${project.id}/source`;
	const selected = sourceSections.find(item => item.key === active);
	const fileRef = useRef<HTMLInputElement>(null);
	const [documents, setDocuments] = useState(initialDocuments);
	const [activity, setActivity] = useState(initialActivity);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [showUpload, setShowUpload] = useState(false);
	const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
	const [dragging, setDragging] = useState(false);
	const [preview, setPreview] = useState<Source | null>(null);
	const [folders, setFolders] = useState(initialFolders);
	const [currentFolderId, setCurrentFolderId] = useState<string | null>(
		null,
	);
	const [showNewFolder, setShowNewFolder] = useState(false);
	const [folderName, setFolderName] = useState('');
	const hasActive = documents.some(item =>
		['uploaded', 'queued', 'processing'].includes(item.status),
	);

	useEffect(() => {
		if (!hasActive) return;
		const timer = window.setInterval(async () => {
			const [documentResult, activityResult] =
				await Promise.all([
					json<{ sources: Source[] }>(
						`/api/knowledge-bases/${source.id}/sources`,
					),
					json<{
						events: KnowledgeActivityEvent[];
					}>(
						`/api/knowledge-bases/${source.id}/activity`,
					),
				]).catch(() => [null, null] as const);
			if (documentResult)
				setDocuments(documentResult.sources);
			if (activityResult) setActivity(activityResult.events);
		}, 2500);
		return () => window.clearInterval(timer);
	}, [hasActive, project.id, source.id]);

	function chooseFiles(files: File[]) {
		setError(null);
		if (files.length > 5) {
			setSelectedFiles([]);
			setError(
				'You can upload a maximum of 5 files at a time.',
			);
			return;
		}
		setSelectedFiles(files);
	}

	function drop(event: DragEvent<HTMLDivElement>) {
		event.preventDefault();
		setDragging(false);
		chooseFiles(Array.from(event.dataTransfer.files));
	}

	async function upload() {
		if (!selectedFiles.length) return;
		setBusy(true);
		setError(null);
		try {
			for (const file of selectedFiles) {
				const form = new FormData();
				form.set('file', file);
				if (currentFolderId)
					form.set('folder_id', currentFolderId);
				const uploaded = await json<Source>(
					`/api/knowledge-bases/${source.id}/sources`,
					{ method: 'POST', body: form },
				);
				setDocuments(current => [
					uploaded,
					...current.filter(
						item => item.id !== uploaded.id,
					),
				]);
			}
			setActivity(
				(
					await json<{
						events: KnowledgeActivityEvent[];
					}>(
						`/api/knowledge-bases/${source.id}/activity`,
					)
				).events,
			);
			setSelectedFiles([]);
			setShowUpload(false);
			if (fileRef.current) fileRef.current.value = '';
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Upload failed',
			);
		} finally {
			setBusy(false);
		}
	}

	async function createFolder() {
		if (!folderName.trim()) return;
		setBusy(true);
		setError(null);
		try {
			const folder = await json<KnowledgeFolder>(
				`/api/knowledge-bases/${source.id}/folders`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						name: folderName.trim(),
						parent_id: currentFolderId,
					}),
				},
			);
			setFolders(current => [...current, folder]);
			setFolderName('');
			setShowNewFolder(false);
			setActivity(
				(
					await json<{
						events: KnowledgeActivityEvent[];
					}>(
						`/api/knowledge-bases/${source.id}/activity`,
					)
				).events,
			);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not create folder',
			);
		} finally {
			setBusy(false);
		}
	}

	function documentExplorer() {
		const visibleFolders = folders.filter(
			folder => folder.parent_id === currentFolderId,
		);
		const visibleDocuments = documents.filter(
			document => document.folder_id === currentFolderId,
		);
		const path: KnowledgeFolder[] = [];
		let cursor = currentFolderId;
		while (cursor) {
			const folder = folders.find(item => item.id === cursor);
			if (!folder) break;
			path.unshift(folder);
			cursor = folder.parent_id;
		}
		return (
			<section className='source-data-panel'>
				<header>
					<div>
						<h2>Documents</h2>
						<p>
							Files and folders
							available to this
							knowledge base.
						</p>
					</div>
					<button
						className='secondary-action folder-create-action'
						onClick={() =>
							setShowNewFolder(true)
						}>
						<FolderPlus size={14} />
						New folder
					</button>
				</header>
				<nav
					className='folder-breadcrumbs'
					aria-label='Folder path'>
					<button
						onClick={() =>
							setCurrentFolderId(null)
						}>
						Knowledge Base
					</button>
					{path.map(folder => (
						<span key={folder.id}>
							<ChevronRight
								size={13}
							/>
							<button
								onClick={() =>
									setCurrentFolderId(
										folder.id,
									)
								}>
								{folder.name}
							</button>
						</span>
					))}
				</nav>
				<div className='knowledge-activity-table-wrap'>
					<table className='knowledge-activity-table document-explorer-table'>
						<thead>
							<tr>
								<th>Name</th>
								<th>Type</th>
								<th>Version</th>
								<th>Size</th>
								<th>
									Modified
								</th>
								<th aria-label='Actions' />
							</tr>
						</thead>
						<tbody>
							{visibleFolders.map(
								folder => (
									<tr
										key={
											folder.id
										}
										className='folder-row'
										onDoubleClick={() =>
											setCurrentFolderId(
												folder.id,
											)
										}>
										<td>
											<button
												className='folder-name-button'
												onClick={() =>
													setCurrentFolderId(
														folder.id,
													)
												}>
												<span className='knowledge-file-icon'>
													<Folder
														size={
															15
														}
													/>
												</span>
												<strong>
													{
														folder.name
													}
												</strong>
											</button>
										</td>
										<td>
											Folder
										</td>
										<td>
											—
										</td>
										<td>
											—
										</td>
										<td>
											<time
												dateTime={
													folder.created_at
												}>
												{new Date(
													folder.created_at,
												).toLocaleString()}
											</time>
										</td>
										<td />
									</tr>
								),
							)}
							{visibleDocuments.map(
								document => (
									<tr
										key={
											document.id
										}>
										<td>
											<span className='knowledge-activity-item'>
												<button
													className='knowledge-file-icon preview-trigger'
													onClick={() =>
														setPreview(
															document,
														)
													}
													aria-label={`View ${document.display_name}`}
													title='View'>
													<Eye
														size={
															15
														}
													/>
												</button>
												<strong>
													{
														document.display_name
													}
												</strong>
											</span>
										</td>
										<td>
											{document.content_type ||
												'Document'}
										</td>
										<td>
											v
											{
												document.version
											}
										</td>
										<td>
											{Math.ceil(
												document.byte_size /
													1024,
											)}{' '}
											KB
										</td>
										<td>
											<time
												dateTime={
													document.created_at
												}>
												{new Date(
													document.created_at,
												).toLocaleString()}
											</time>
										</td>
										<td className='document-row-action'>
											<div>
												<button
													onClick={() =>
														remove(
															document,
														)
													}
													aria-label={`Delete ${document.display_name}`}
													title='Delete'>
													<Trash2
														size={
															14
														}
													/>
												</button>
											</div>
										</td>
									</tr>
								),
							)}
							{visibleFolders.length ===
								0 &&
								visibleDocuments.length ===
									0 && (
									<tr>
										<td
											colSpan={
												6
											}
											className='source-empty'>
											This
											folder
											is
											empty.
										</td>
									</tr>
								)}
						</tbody>
					</table>
				</div>
			</section>
		);
	}

	async function remove(document: Source) {
		if (!window.confirm(`Delete ${document.display_name}?`)) return;
		setError(null);
		try {
			const response = await fetch(
				`/api/knowledge-bases/${source.id}/sources/${document.id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok) throw new Error('Delete failed');
			setDocuments(current =>
				current.filter(item => item.id !== document.id),
			);
			setActivity(
				(
					await json<{
						events: KnowledgeActivityEvent[];
					}>(
						`/api/knowledge-bases/${source.id}/activity`,
					)
				).events,
			);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Delete failed',
			);
		}
	}

	function content() {
		if (active === 'documents') return documentExplorer();
		if (active === 'activity')
			return <KnowledgeActivity events={activity} />;
		return null;
	}
	return (
		<div className='source-foundation'>
			<header className='bot-console-hero'>
				<div className='bot-console-identity'>
					<div>
						<span className='eyebrow'>
							Data
						</span>
						<h1>Knowledge Base</h1>
						<p>
							The governed knowledge
							boundary from which
							index versions are
							built.
						</p>
					</div>
				</div>
				<button
					className='primary-action'
					onClick={() => {
						setError(null);
						setShowUpload(true);
					}}>
					<Upload size={15} />
					Add document
				</button>
			</header>
			<nav
				className='bot-console-tabs'
				aria-label='Knowledge sections'>
				{sourceSections.map(item => (
					<SmoothLink
						key={item.key}
						href={`${base}/${item.key}`}
						className={
							active === item.key
								? 'active'
								: ''
						}>
						{item.title}
					</SmoothLink>
				))}
			</nav>
			{error && (
				<div className='workspace-error'>{error}</div>
			)}
			{selected && (
				<p className='source-section-description'>
					{selected.description}
				</p>
			)}
			{content()}
			{showUpload && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'
					aria-labelledby='knowledge-upload-title'>
					<section className='workspace-modal knowledge-upload-modal'>
						<header>
							<div>
								<h2 id='knowledge-upload-title'>
									Add
									documents
								</h2>
								<p>
									Upload
									up to 5
									files to
									this
									knowledge
									base.
								</p>
							</div>
							<button
								className='icon-action'
								onClick={() => {
									setShowUpload(
										false,
									);
									setSelectedFiles(
										[],
									);
								}}
								aria-label='Close'>
								<X size={18} />
							</button>
						</header>
						{error && (
							<div className='workspace-error'>
								{error}
							</div>
						)}
						<div
							className={`knowledge-dropzone${dragging ? ' dragging' : ''}`}
							onDragEnter={event => {
								event.preventDefault();
								setDragging(
									true,
								);
							}}
							onDragOver={event =>
								event.preventDefault()
							}
							onDragLeave={() =>
								setDragging(
									false,
								)
							}
							onDrop={drop}>
							<Upload size={24} />
							<strong>
								Drop files here
							</strong>
							<span>
								or choose files
								from your
								computer
							</span>
							<label className='secondary-action'>
								Browse files
								<input
									ref={
										fileRef
									}
									type='file'
									multiple
									onChange={event =>
										chooseFiles(
											Array.from(
												event
													.target
													.files ??
													[],
											),
										)
									}
									disabled={
										busy
									}
								/>
							</label>
							<small>
								Maximum 5 files
								per upload
							</small>
						</div>
						{selectedFiles.length > 0 && (
							<div className='knowledge-upload-queue'>
								{selectedFiles.map(
									(
										file,
										index,
									) => (
										<div
											key={`${file.name}-${file.lastModified}`}>
											<FileText
												size={
													16
												}
											/>
											<span>
												<strong>
													{
														file.name
													}
												</strong>
												<small>
													{Math.ceil(
														file.size /
															1024,
													)}{' '}
													KB
												</small>
											</span>
											<button
												onClick={() =>
													setSelectedFiles(
														current =>
															current.filter(
																(
																	_,
																	itemIndex,
																) =>
																	itemIndex !==
																	index,
															),
													)
												}
												aria-label={`Remove ${file.name}`}>
												<X
													size={
														14
													}
												/>
											</button>
										</div>
									),
								)}
							</div>
						)}
						<footer>
							<span>
								{
									selectedFiles.length
								}
								/5 files
								selected
							</span>
							<div>
								<button
									className='secondary-action'
									onClick={() => {
										setShowUpload(
											false,
										);
										setSelectedFiles(
											[],
										);
									}}>
									Cancel
								</button>
								<button
									className='primary-action'
									onClick={
										upload
									}
									disabled={
										busy ||
										selectedFiles.length ===
											0
									}>
									{busy
										? 'Uploading…'
										: `Upload ${selectedFiles.length || ''}`}
								</button>
							</div>
						</footer>
					</section>
				</div>
			)}
			{showNewFolder && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'
					aria-labelledby='new-folder-title'>
					<section className='workspace-modal new-folder-modal'>
						<header>
							<div>
								<h2 id='new-folder-title'>
									New
									folder
								</h2>
								<p>
									Create a
									folder
									in the
									current
									location.
								</p>
							</div>
							<button
								className='icon-action'
								onClick={() =>
									setShowNewFolder(
										false,
									)
								}
								aria-label='Close'>
								<X size={18} />
							</button>
						</header>
						<label>
							Folder name
							<input
								value={
									folderName
								}
								onChange={event =>
									setFolderName(
										event
											.target
											.value,
									)
								}
								maxLength={160}
								autoFocus
								onKeyDown={event => {
									if (
										event.key ===
										'Enter'
									)
										createFolder();
								}}
							/>
						</label>
						<footer>
							<button
								className='secondary-action'
								onClick={() =>
									setShowNewFolder(
										false,
									)
								}>
								Cancel
							</button>
							<button
								className='primary-action'
								onClick={
									createFolder
								}
								disabled={
									busy ||
									!folderName.trim()
								}>
								{busy
									? 'Creating…'
									: 'Create folder'}
							</button>
						</footer>
					</section>
				</div>
			)}
			{preview && (
				<div
					className='document-preview-backdrop'
					role='dialog'
					aria-modal='true'
					aria-labelledby='document-preview-title'>
					<section className='document-preview-panel'>
						<header>
							<div>
								<span className='eyebrow'>
									Document
									preview
								</span>
								<h2 id='document-preview-title'>
									{
										preview.display_name
									}
								</h2>
								<p>
									Version{' '}
									{
										preview.version
									}{' '}
									·{' '}
									{Math.ceil(
										preview.byte_size /
											1024,
									)}{' '}
									KB
								</p>
							</div>
							<button
								onClick={() =>
									setPreview(
										null,
									)
								}
								aria-label='Close preview'>
								<X size={18} />
							</button>
						</header>
						<div className='document-preview-content'>
							{preview.content_type.startsWith(
								'image/',
							) ? (
								<Image
									unoptimized
									width={
										1200
									}
									height={
										900
									}
									src={`/api/knowledge-bases/${source.id}/sources/${preview.id}/file`}
									alt={
										preview.display_name
									}
								/>
							) : (
								<iframe
									title={
										preview.display_name
									}
									src={`/api/knowledge-bases/${source.id}/sources/${preview.id}/file#toolbar=0&navpanes=0`}
								/>
							)}
						</div>
					</section>
				</div>
			)}
		</div>
	);
}

function KnowledgeActivity({ events }: { events: KnowledgeActivityEvent[] }) {
	return (
		<section className='source-data-panel'>
			<header>
				<div>
					<h2>Audit history</h2>
					<p>
						Immutable document and folder
						events recorded for this
						knowledge base.
					</p>
				</div>
			</header>
			<div className='knowledge-activity-table-wrap'>
				<table className='knowledge-activity-table'>
					<thead>
						<tr>
							<th>Name</th>
							<th>Event</th>
							<th>Version</th>
							<th>Details</th>
							<th>Occurred</th>
						</tr>
					</thead>
					<tbody>
						{events.map(event => {
							const deleted =
								event.event_type ===
								'knowledge.document_deleted';
							const folder =
								event.event_type ===
								'knowledge.folder_created';
							const Icon = folder
								? Folder
								: deleted
									? Trash2
									: Upload;
							return (
								<tr
									key={
										event.id
									}>
									<td>
										<span className='knowledge-activity-item'>
											<span className='knowledge-file-icon'>
												<Icon
													size={
														15
													}
												/>
											</span>
											<strong>
												{folder
													? event
															.payload
															.name
													: event
															.payload
															.filename ||
														'Document'}
											</strong>
										</span>
									</td>
									<td>
										{folder
											? 'Folder created'
											: deleted
												? 'Deleted'
												: 'Uploaded'}
									</td>
									<td>
										{event
											.payload
											.version
											? `v${event.payload.version}`
											: '—'}
									</td>
									<td>
										{event
											.payload
											.byte_size
											? `${Math.ceil(event.payload.byte_size / 1024)} KB`
											: '—'}
									</td>
									<td>
										<time
											dateTime={
												event.occurred_at
											}>
											{new Date(
												event.occurred_at,
											).toLocaleString()}
										</time>
									</td>
								</tr>
							);
						})}
						{events.length === 0 && (
							<tr>
								<td
									colSpan={
										5
									}
									className='source-empty'>
									No audit
									events
									yet.
								</td>
							</tr>
						)}
					</tbody>
				</table>
			</div>
		</section>
	);
}
