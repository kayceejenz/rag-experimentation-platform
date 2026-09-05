'use client';
import { FormEvent, useState } from 'react';
import {
	Binary,
	Blocks,
	Braces,
	Eye,
	FileText,
	Layers3,
	Plus,
	RefreshCw,
	Trash2,
	X,
} from 'lucide-react';
import type {
	KnowledgeBase,
	KnowledgeFolder,
	Project,
	Source,
} from '@/types/workspace';
import { formatDateTime } from '@/lib/format';

type EmbeddingModel = {
	id: string;
	provider: string;
	model_name: string;
	dimensions: number;
	distance_metric: string;
	configuration: Record<string, unknown>;
};
type Strategy = { id: string; name: string; provider: string };
type IndexBuild = {
	id: string;
	configuration: {
		name: string;
		chunking: { strategy: string };
		knowledge?: { scope: 'root' | 'folders'; folder_ids: string[] };
		embedding: {
			provider: string;
			model: string;
			dimensions: number;
		};
	};
	configuration_hash: string;
	created_at: string;
	job_count: number;
	completed_jobs: number;
	failed_jobs: number;
	active_jobs: number;
};
export type IndexCatalog = {
	embedding_models: EmbeddingModel[];
	chunking_strategies: Strategy[];
	indexes: IndexBuild[];
};
type Artifact = {
	id: string;
	kind: string;
	role: string;
	storage_type: string;
	storage_key: string | null;
	manifest: Record<string, unknown> | null;
};
type IndexTrace = {
	id: string;
	kind: string;
	status: string;
	worker_id: string | null;
	attempt: number;
	parameters: Record<string, unknown>;
	created_at: string;
	started_at: string | null;
	completed_at: string | null;
	error_message: string | null;
	inputs: Artifact[];
	outputs: Artifact[];
};
type IndexDetail = {
	specification: IndexBuild;
	jobs: Array<{
		id: string;
		stage: string;
		status: string;
		display_name: string;
		version: number;
		source_version_id: string;
		created_at: string;
	}>;
	traces: IndexTrace[];
};
type ArtifactPreview = {
	artifact: Artifact;
	records: Array<Record<string, unknown>>;
	limit: number;
};

function shortId(value: unknown) {
	const id = String(value ?? '—');
	return id.length > 14 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id;
}

function vectorPreview(value: unknown) {
	const vector = String(value ?? '[]');
	const values = vector.slice(1, -1).split(',');
	return values.length > 8
		? `[${values.slice(0, 8).join(', ')}, …]`
		: vector;
}

function traceDuration(trace: IndexTrace) {
	if (!trace.started_at) return '—';
	if (!trace.completed_at) return 'In progress';
	const end = new Date(trace.completed_at).getTime();
	const milliseconds = Math.max(
		0,
		end - new Date(trace.started_at).getTime(),
	);
	if (milliseconds < 1000) return `${milliseconds} ms`;
	if (milliseconds < 60_000)
		return `${(milliseconds / 1000).toFixed(1)} s`;
	return `${Math.floor(milliseconds / 60_000)}m ${Math.floor((milliseconds % 60_000) / 1000)}s`;
}

function traceOperation(kind: string) {
	if (kind === 'chunking') return 'Elements & chunks';
	if (kind === 'index_build') return 'Embedding index';
	return kind.replaceAll('_', ' ');
}

function ArtifactPreviewTable({ preview }: { preview: ArtifactPreview }) {
	if (!preview.records.length)
		return (
			<p className='artifact-preview-empty'>
				This output contains no records.
			</p>
		);
	if (preview.artifact.kind === 'element_dataset')
		return (
			<table>
				<thead>
					<tr>
						<th>#</th>
						<th>Category</th>
						<th>Content</th>
						<th>Page</th>
						<th>Element ID</th>
					</tr>
				</thead>
				<tbody>
					{preview.records.map(
						(record, position) => (
							<tr
								key={String(
									record.element_id ??
										position,
								)}>
								<td>
									{Number(
										record.sequence_number ??
											position,
									) + 1}
								</td>
								<td>
									<span className='artifact-type-value'>
										{String(
											record.category ??
												'Text',
										)}
									</span>
								</td>
								<td className='artifact-content-cell'>
									{String(
										record.content ??
											'—',
									)}
								</td>
								<td>
									{String(
										record.page_number ??
											'—',
									)}
								</td>
								<td>
									<code>
										{shortId(
											record.element_id,
										)}
									</code>
								</td>
							</tr>
						),
					)}
				</tbody>
			</table>
		);
	if (preview.artifact.kind === 'chunk_dataset')
		return (
			<table>
				<thead>
					<tr>
						<th>#</th>
						<th>Content</th>
						<th>Pages</th>
						<th>Chunk ID</th>
					</tr>
				</thead>
				<tbody>
					{preview.records.map(
						(record, position) => (
							<tr
								key={String(
									record.id ??
										position,
								)}>
								<td>
									{Number(
										record.position ??
											position,
									) + 1}
								</td>
								<td className='artifact-content-cell'>
									{String(
										record.content ??
											'—',
									)}
								</td>
								<td>
									{record.page_from ==
									null
										? '—'
										: record.page_from ===
											  record.page_to
											? String(
													record.page_from,
												)
											: `${String(record.page_from)}–${String(record.page_to)}`}
								</td>
								<td>
									<code>
										{shortId(
											record.id,
										)}
									</code>
								</td>
							</tr>
						),
					)}
				</tbody>
			</table>
		);
	return (
		<table>
			<thead>
				<tr>
					<th>#</th>
					<th>Model</th>
					<th>Dimensions</th>
					<th>Vector preview</th>
					<th>Chunk ID</th>
				</tr>
			</thead>
			<tbody>
				{preview.records.map((record, position) => (
					<tr
						key={String(
							record.chunk_id ??
								position,
						)}>
						<td>{position + 1}</td>
						<td>
							<span className='artifact-model-value'>
								{String(
									record.provider ??
										'—',
								)}{' '}
								/{' '}
								{String(
									record.model_name ??
										'—',
								)}
							</span>
						</td>
						<td>
							{String(
								record.dimensions ??
									'—',
							)}
						</td>
						<td className='artifact-vector-cell'>
							<code
								title={String(
									record.embedding ??
										'',
								)}>
								{vectorPreview(
									record.embedding,
								)}
							</code>
						</td>
						<td>
							<code>
								{shortId(
									record.chunk_id,
								)}
							</code>
						</td>
					</tr>
				))}
			</tbody>
		</table>
	);
}

export function IndexManager({
	project,
	knowledgeBase,
	folders,
	sources,
	initialCatalog,
}: {
	project: Project;
	knowledgeBase: KnowledgeBase;
	folders: KnowledgeFolder[];
	sources: Source[];
	initialCatalog: IndexCatalog;
}) {
	const [catalog, setCatalog] = useState(initialCatalog);
	const [showCreate, setShowCreate] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [notice, setNotice] = useState<string | null>(null);
	const [detail, setDetail] = useState<IndexDetail | null>(null);
	const [detailTab, setDetailTab] = useState<
		'overview' | 'inputs' | 'outputs' | 'traces'
	>('overview');
	const [preview, setPreview] = useState<ArtifactPreview | null>(null);
	const [confirmDelete, setConfirmDelete] = useState(false);
	const [selectedFolderIds, setSelectedFolderIds] = useState<string[]>(
		[],
	);
	const folderById = new Map(folders.map(folder => [folder.id, folder]));
	function folderLabel(folder: KnowledgeFolder) {
		const names = [folder.name];
		let parentId = folder.parent_id;
		while (parentId) {
			const parent = folderById.get(parentId);
			if (!parent) break;
			names.unshift(parent.name);
			parentId = parent.parent_id;
		}
		return names.join(' / ');
	}
	const orderedFolders = [...folders].sort((left, right) =>
		folderLabel(left).localeCompare(folderLabel(right)),
	);
	async function inspect(indexId: string) {
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/indexes/${indexId}`,
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body?.detail ?? 'Could not load index.',
				);
			setDetail(body);
			setDetailTab('overview');
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not load index.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function previewArtifact(artifact: Artifact) {
		if (!detail) return;
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/indexes/${detail.specification.id}/artifacts/${artifact.id}/preview`,
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body?.detail ??
						'Could not preview output.',
				);
			setPreview(body);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not preview output.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function refreshIndex() {
		if (!detail) return;
		setBusy(true);
		setError(null);
		setNotice(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/indexes/${detail.specification.id}/refresh`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						knowledge_base_id:
							knowledgeBase.id,
					}),
				},
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body?.detail ??
						'Could not refresh index.',
				);
			setNotice(
				body.new_sources
					? `${body.new_sources} new file${body.new_sources === 1 ? '' : 's'} queued for indexing.`
					: 'Index is up to date. No new files were found.',
			);
			const [detailResponse, catalogResponse] =
				await Promise.all([
					fetch(
						`/api/projects/${project.id}/indexes/${detail.specification.id}`,
					),
					fetch(
						`/api/projects/${project.id}/indexes`,
					),
				]);
			setDetail(await detailResponse.json());
			setCatalog(await catalogResponse.json());
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not refresh index.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function deleteIndex() {
		if (!detail) return;
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/indexes/${detail.specification.id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok) {
				const body = await response
					.json()
					.catch(() => ({}));
				throw new Error(
					body?.detail ??
						'Could not delete index.',
				);
			}
			setCatalog(current => ({
				...current,
				indexes: current.indexes.filter(
					index =>
						index.id !==
						detail.specification.id,
				),
			}));
			setConfirmDelete(false);
			setPreview(null);
			setDetail(null);
			setNotice(
				'Index deleted. Its completed lineage remains preserved.',
			);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not delete index.',
			);
		} finally {
			setBusy(false);
		}
	}
	function artifactIcon(kind: string) {
		if (kind === 'element_dataset') return <Braces size={15} />;
		if (kind === 'chunk_dataset') return <Blocks size={15} />;
		if (kind === 'embedding_dataset') return <Binary size={15} />;
		return <FileText size={15} />;
	}

	async function create(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setBusy(true);
		setError(null);
		const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/indexes`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						name: form.get('name'),
						knowledge_base_id:
							knowledgeBase.id,
						embedding_model_id:
							form.get(
								'embedding_model_id',
							),
						chunking_strategy:
							form.get(
								'chunking_strategy',
							),
						folder_ids: selectedFolderIds,
					}),
				},
			);
			const body = await response.json().catch(() => ({}));
			if (!response.ok)
				throw new Error(
					body?.error?.message ??
						body?.detail ??
						'Could not create index.',
				);
			const refreshed = await fetch(
				`/api/projects/${project.id}/indexes`,
			);
			setCatalog(await refreshed.json());
			setShowCreate(false);
			setSelectedFolderIds([]);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not create index.',
			);
		} finally {
			setBusy(false);
		}
	}

	function buildStatus(build: IndexBuild) {
		if (build.failed_jobs) return 'Failed';
		if (build.active_jobs) return 'Building';
		if (build.job_count && build.completed_jobs === build.job_count)
			return 'Ready';
		return 'Pending';
	}
	return (
		<div className='catalog-page index-manager'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>Data</span>
					<h1>Indexes</h1>
					<p>
						Create immutable vector indexes
						from the Knowledge Base using
						explicit chunking and embedding
						specifications.
					</p>
				</div>
				<button
					className='primary-action'
					onClick={() => setShowCreate(true)}
					disabled={
						!catalog.embedding_models.length
					}>
					<Plus size={15} />
					Create Index
				</button>
			</header>
			{error && !detail && (
				<div className='workspace-error'>{error}</div>
			)}
			{notice && !detail && (
				<div className='workspace-notice'>{notice}</div>
			)}
			<section className='catalog-table-panel'>
				<header>
					<div>
						<h2>Vector indexes</h2>
						<p>
							{catalog.indexes.length}{' '}
							configured
						</p>
					</div>
				</header>
				<div className='catalog-table-wrap'>
					<table>
						<thead>
							<tr>
								<th>Name</th>
								<th>
									Embedding
									model
								</th>
								<th>
									Dimensions
								</th>
								<th>
									Chunking
								</th>
								<th>Jobs</th>
								<th>Status</th>
								<th>Created</th>
								<th aria-label='Actions' />
							</tr>
						</thead>
						<tbody>
							{catalog.indexes.map(
								build => (
									<tr
										key={
											build.id
										}>
										<td>
											<span className='catalog-primary'>
												<Layers3
													size={
														14
													}
												/>
												<strong>
													{
														build
															.configuration
															.name
													}
												</strong>
											</span>
										</td>
										<td>
											{
												build
													.configuration
													.embedding
													.model
											}
										</td>
										<td>
											{
												build
													.configuration
													.embedding
													.dimensions
											}
										</td>
										<td>
											Unstructured
											/{' '}
											{
												build
													.configuration
													.chunking
													.strategy
											}
										</td>
										<td>
											{
												build.completed_jobs
											}

											/
											{
												build.job_count
											}
										</td>
										<td>
											<span
												className={`catalog-state ${buildStatus(build).toLowerCase()}`}>
												{buildStatus(
													build,
												)}
											</span>
										</td>
										<td>
											{formatDateTime(build.created_at)}
										</td>
										<td className='catalog-open'>
											<button
												onClick={() =>
													inspect(
														build.id,
													)
												}
												disabled={
													busy
												}
												aria-label={`Inspect ${build.configuration.name}`}>
												<Eye
													size={
														14
													}
												/>
											</button>
										</td>
									</tr>
								),
							)}
							{!catalog.indexes
								.length && (
								<tr>
									<td
										colSpan={
											8
										}
										className='mock-empty'>
										No
										indexes
										configured
										yet.
									</td>
								</tr>
							)}
						</tbody>
					</table>
				</div>
			</section>
			{showCreate && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'>
					<form
						className='workspace-modal index-create-modal'
						onSubmit={create}>
						<div className='modal-title'>
							<div>
								<h2>
									Create
									index
								</h2>
								<p>
									The
									configuration
									is saved
									as an
									immutable
									specification.
								</p>
							</div>
							<button
								type='button'
								className='icon-action'
								onClick={() => {
									setShowCreate(
										false,
									);
									setSelectedFolderIds(
										[],
									);
								}}
								aria-label='Close'>
								<X size={18} />
							</button>
						</div>
						<div className='project-form-fields'>
							<label>
								Index name
								<input
									name='name'
									required
									minLength={
										2
									}
									maxLength={
										160
									}
									autoFocus
								/>
							</label>
							<label>
								Knowledge Base
								<input
									value={
										knowledgeBase.name
									}
									disabled
								/>
							</label>
							<fieldset className='index-folder-selector'>
								<legend>
									Knowledge
									folders
								</legend>
								<p>
									Select
									Root for
									every
									file, or
									choose
									the
									folders
									this
									Index
									should
									contain.
								</p>
								<label className='index-folder-option root'>
									<input
										type='checkbox'
										checked={
											!selectedFolderIds.length
										}
										onChange={() =>
											setSelectedFolderIds(
												[],
											)
										}
									/>
									<span>
										<strong>
											Root
										</strong>
										<small>
											{
												sources.length
											}{' '}
											files
											across
											the
											Knowledge
											Base
										</small>
									</span>
								</label>
								<div className='index-folder-options'>
									{orderedFolders.map(
										folder => {
											const directFiles =
												sources.filter(
													source =>
														source.folder_id ===
														folder.id,
												).length;
											return (
												<label
													className='index-folder-option'
													key={
														folder.id
													}>
													<input
														type='checkbox'
														checked={selectedFolderIds.includes(
															folder.id,
														)}
														onChange={() =>
															setSelectedFolderIds(
																current =>
																	current.includes(
																		folder.id,
																	)
																		? current.filter(
																				id =>
																					id !==
																					folder.id,
																			)
																		: [
																				...current,
																				folder.id,
																			],
															)
														}
													/>
													<span>
														<strong>
															{folderLabel(
																folder,
															)}
														</strong>
														<small>
															{
																directFiles
															}{' '}
															direct
															file
															{directFiles ===
															1
																? ''
																: 's'}{' '}
															·
															includes
															subfolders
														</small>
													</span>
												</label>
											);
										},
									)}
									{!orderedFolders.length && (
										<p className='artifact-preview-empty'>
											No
											folders
											yet.
											Root
											will
											index
											the
											full
											Knowledge
											Base.
										</p>
									)}
								</div>
							</fieldset>
							<label>
								Embedding model
								<select
									name='embedding_model_id'
									required>
									{catalog.embedding_models.map(
										model => (
											<option
												key={
													model.id
												}
												value={
													model.id
												}>
												{
													model.model_name
												}{' '}
												·{' '}
												{
													model.dimensions
												}{' '}
												dimensions
												·{' '}
												{
													model.distance_metric
												}
											</option>
										),
									)}
								</select>
							</label>
							<label>
								Chunking
								strategy
								<select
									name='chunking_strategy'
									required
									defaultValue='by_title'>
									{catalog.chunking_strategies.map(
										strategy => (
											<option
												key={
													strategy.id
												}
												value={
													strategy.id
												}>
												{
													strategy.provider
												}{' '}
												/{' '}
												{
													strategy.name
												}
											</option>
										),
									)}
								</select>
							</label>
						</div>
						<div className='index-spec-summary'>
							<strong>
								Build flow
							</strong>
							<span>
								{selectedFolderIds.length
									? `${selectedFolderIds.length} selected folder${selectedFolderIds.length === 1 ? '' : 's'}`
									: 'Knowledge Base Root'}{' '}
								→ Unstructured
								chunking →
								Embeddings →
								Vector index
							</span>
						</div>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={() => {
									setShowCreate(
										false,
									);
									setSelectedFolderIds(
										[],
									);
								}}>
								Cancel
							</button>
							<button
								className='primary-action'
								disabled={busy}>
								{busy
									? 'Starting…'
									: 'Create and build'}
							</button>
						</div>
					</form>
				</div>
			)}
			{detail && (
				<div
					className='index-detail-backdrop'
					role='dialog'
					aria-modal='true'>
					<section className='index-detail-panel'>
						<header>
							<div>
								<span className='eyebrow'>
									Vector
									index
								</span>
								<h2>
									{
										detail
											.specification
											.configuration
											.name
									}
								</h2>
								<p>
									{
										detail
											.specification
											.configuration_hash
									}
								</p>
							</div>
							<div className='index-detail-actions'>
								<button
									onClick={
										refreshIndex
									}
									disabled={
										busy
									}>
									<RefreshCw
										size={
											14
										}
										className={
											busy
												? 'spinning'
												: ''
										}
									/>
									{busy
										? 'Checking…'
										: 'Refresh index'}
								</button>
								<button
									className='index-delete-action'
									onClick={() =>
										setConfirmDelete(
											true,
										)
									}
									disabled={
										busy
									}
									aria-label='Delete index'>
									<Trash2
										size={
											14
										}
									/>
								</button>
								<button
									onClick={() => {
										setDetail(
											null,
										);
										setPreview(
											null,
										);
									}}
									aria-label='Close'>
									<X
										size={
											18
										}
									/>
								</button>
							</div>
						</header>
						<nav>
							{(
								[
									'overview',
									'inputs',
									'outputs',
									'traces',
								] as const
							).map(tab => (
								<button
									key={
										tab
									}
									className={
										detailTab ===
										tab
											? 'active'
											: ''
									}
									onClick={() =>
										setDetailTab(
											tab,
										)
									}>
									{tab}
								</button>
							))}
						</nav>
						{!preview &&
							(error || notice) && (
								<div className='index-panel-alerts'>
									{error && (
										<div className='workspace-error'>
											{
												error
											}
										</div>
									)}
									{notice && (
										<div className='workspace-notice'>
											{
												notice
											}
										</div>
									)}
								</div>
							)}
						<div className='index-detail-body'>
							{detailTab ===
								'overview' && (
								<dl className='index-overview-simple'>
									<div>
										<dt>
											Embedding
										</dt>
										<dd>
											{
												detail
													.specification
													.configuration
													.embedding
													.model
											}
										</dd>
									</div>
									<div>
										<dt>
											Dimensions
										</dt>
										<dd>
											{
												detail
													.specification
													.configuration
													.embedding
													.dimensions
											}
										</dd>
									</div>
									<div>
										<dt>
											Chunking
										</dt>
										<dd>
											Unstructured
											/{' '}
											{
												detail
													.specification
													.configuration
													.chunking
													.strategy
											}
										</dd>
									</div>
									<div>
										<dt>
											Knowledge
											scope
										</dt>
										<dd>
											{detail
												.specification
												.configuration
												.knowledge
												?.scope ===
											'folders'
												? `${detail.specification.configuration.knowledge.folder_ids.length} selected folder${detail.specification.configuration.knowledge.folder_ids.length === 1 ? '' : 's'}`
												: 'Root · all files'}
										</dd>
									</div>
									<div>
										<dt>
											Progress
										</dt>
										<dd>
											{
												detail.jobs.filter(
													job =>
														job.status ===
														'completed',
												)
													.length
											}{' '}
											of{' '}
											{
												detail
													.jobs
													.length
											}{' '}
											jobs
											completed
										</dd>
									</div>
								</dl>
							)}
							{detailTab ===
								'inputs' && (
								<div className='index-detail-list'>
									{detail.jobs
										.filter(
											job =>
												job.stage ===
												'chunk',
										)
										.map(
											job => (
												<div
													key={
														job.id
													}>
													<FileText
														size={
															15
														}
													/>
													<span>
														<strong>
															{
																job.display_name
															}
														</strong>
														<small>
															Version{' '}
															{
																job.version
															}
														</small>
													</span>
													<em>
														{
															job.status
														}
													</em>
												</div>
											),
										)}
									{!detail.jobs.some(
										job =>
											job.stage ===
											'chunk',
									) && (
										<p>
											No
											inputs
											recorded.
										</p>
									)}
								</div>
							)}
							{detailTab ===
								'outputs' && (
								<div className='index-detail-list index-output-list'>
									{detail.traces.flatMap(
										trace =>
											trace.outputs.map(
												output => (
													<div
														key={`${trace.id}-${output.id}`}>
														<span
															className={`artifact-kind-icon ${output.kind}`}>
															{artifactIcon(
																output.kind,
															)}
														</span>
														<span>
															<strong>
																{
																	output.role
																}
															</strong>
															<small>
																{output.kind.replaceAll(
																	'_',
																	' ',
																)}{' '}
																·{' '}
																{String(
																	output
																		.manifest
																		?.row_count ??
																		0,
																)}{' '}
																records
															</small>
														</span>
														<button
															onClick={() =>
																previewArtifact(
																	output,
																)
															}
															disabled={
																busy
															}
															aria-label={`Preview ${output.role}`}>
															<Eye
																size={
																	14
																}
															/>
														</button>
													</div>
												),
											),
									)}
									{!detail.traces.some(
										trace =>
											trace
												.outputs
												.length,
									) && (
										<p>
											No
											outputs
											produced
											yet.
										</p>
									)}
								</div>
							)}
							{detailTab ===
								'traces' && (
								<div className='index-trace-table-wrap'>
									<table>
										<thead>
											<tr>
												<th>
													#
												</th>
												<th>
													Document
												</th>
												<th>
													Operation
												</th>
												<th>
													Status
												</th>
												<th>
													Duration
												</th>
												<th>
													Started
												</th>
												<th>
													Attempt
												</th>
											</tr>
										</thead>
										<tbody>
											{detail.traces.map(
												(
													trace,
													position,
												) => {
													const sourceVersionId =
														String(
															trace
																.parameters
																?.source_version_id ??
																'',
														);
													const source =
														detail.jobs.find(
															job =>
																job.source_version_id ===
																sourceVersionId,
														);
													return (
														<tr
															key={
																trace.id
															}
															className={
																trace.error_message
																	? 'trace-row-error'
																	: ''
															}>
															<td>
																{position +
																	1}
															</td>
															<td>
																<strong>
																	{source?.display_name ??
																		'Unknown document'}
																</strong>
																<small>
																	{source
																		? `Version ${source.version}`
																		: shortId(
																				sourceVersionId,
																			)}
																</small>
															</td>
															<td>
																<strong>
																	{traceOperation(
																		trace.kind,
																	)}
																</strong>
																{trace.error_message && (
																	<small>
																		{
																			trace.error_message
																		}
																	</small>
																)}
															</td>
															<td>
																<em
																	className={`catalog-state ${trace.status}`}>
																	{
																		trace.status
																	}
																</em>
															</td>
															<td>
																{traceDuration(
																	trace,
																)}
															</td>
															<td>
																{trace.started_at
																			? formatDateTime(
																					trace.started_at,
																				)
																	: 'Not started'}
															</td>
															<td>
																{
																	trace.attempt
																}
															</td>
														</tr>
													);
												},
											)}
										</tbody>
									</table>
									{!detail
										.traces
										.length && (
										<p>
											No
											execution
											traces
											yet.
										</p>
									)}
								</div>
							)}
						</div>
					</section>
					{preview && (
						<section className='artifact-preview-panel'>
							<header>
								<div>
									<span
										className={`artifact-kind-icon ${preview.artifact.kind}`}>
										{artifactIcon(
											preview
												.artifact
												.kind,
										)}
									</span>
									<span>
										<strong>
											{preview.artifact.kind.replaceAll(
												'_',
												' ',
											)}
										</strong>
										<small>
											{
												preview
													.records
													.length
											}{' '}
											records
											shown
										</small>
									</span>
								</div>
								<button
									onClick={() =>
										setPreview(
											null,
										)
									}
									aria-label='Close preview'>
									<X
										size={
											18
										}
									/>
								</button>
							</header>
							{(error || notice) && (
								<div className='index-panel-alerts'>
									{error && (
										<div className='workspace-error'>
											{
												error
											}
										</div>
									)}
									{notice && (
										<div className='workspace-notice'>
											{
												notice
											}
										</div>
									)}
								</div>
							)}
							<div className='artifact-preview-table-wrap'>
								<ArtifactPreviewTable
									preview={
										preview
									}
								/>
							</div>
						</section>
					)}
				</div>
			)}
			{confirmDelete && detail && (
				<div
					className='modal-backdrop index-delete-confirm'
					role='dialog'
					aria-modal='true'>
					<section className='workspace-modal project-action-modal'>
						<div className='modal-title'>
							<div>
								<h2>
									Delete
									index?
								</h2>
								<p>
									<strong>
										{
											detail
												.specification
												.configuration
												.name
										}
									</strong>{' '}
									will be
									removed
									from the
									index
									catalog.
									Completed
									lineage
									will
									remain
									preserved.
								</p>
							</div>
							<button
								className='icon-action'
								onClick={() =>
									setConfirmDelete(
										false,
									)
								}
								aria-label='Close'>
								<X size={18} />
							</button>
						</div>
						<div className='project-form-actions'>
							<button
								className='secondary-action'
								onClick={() =>
									setConfirmDelete(
										false,
									)
								}>
								Cancel
							</button>
							<button
								className='danger-action'
								onClick={
									deleteIndex
								}
								disabled={busy}>
								{busy
									? 'Deleting…'
									: 'Delete index'}
							</button>
						</div>
					</section>
				</div>
			)}
		</div>
	);
}
