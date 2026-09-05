'use client';
import { FormEvent, useState } from 'react';
import {
	Archive,
	ChevronRight,
	FileCode2,
	ListFilter,
	Plus,
	X,
} from 'lucide-react';
import type { Project, PromptAsset, PromptVersion } from '@/types/workspace';
import { formatDateTime } from '@/lib/format';
type Detail = { prompt: PromptAsset; versions: PromptVersion[] };
type PromptTypeFilter = 'all' | PromptAsset['prompt_type'];
export function PromptManager({
	project,
	initialPrompts,
}: {
	project: Project;
	initialPrompts: PromptAsset[];
}) {
	const [prompts, setPrompts] = useState(initialPrompts),
		[detail, setDetail] = useState<Detail | null>(null),
		[createOpen, setCreateOpen] = useState(false),
		[versionOpen, setVersionOpen] = useState(false),
		[typeFilter, setTypeFilter] = useState<PromptTypeFilter>('all'),
		[busy, setBusy] = useState(false),
		[error, setError] = useState<string | null>(null);
	const canManage =
		project.role === 'owner' || project.permissions?.prompts?.manage;
	const visiblePrompts =
		typeFilter === 'all'
			? prompts
			: prompts.filter(prompt => prompt.prompt_type === typeFilter);
	async function inspect(id: string) {
		setBusy(true);
		setError(null);
		try {
			const r = await fetch(
					`/api/projects/${project.id}/prompts/${id}`,
				),
				b = await r.json();
			if (!r.ok)
				throw new Error(
					b.detail ?? 'Could not load prompt.',
				);
			setDetail(b);
		} catch (e) {
			setError(
				e instanceof Error
					? e.message
					: 'Could not load prompt.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function create(e: FormEvent<HTMLFormElement>) {
		e.preventDefault();
		setBusy(true);
		setError(null);
		const f = new FormData(e.currentTarget);
		try {
			const r = await fetch(
					`/api/projects/${project.id}/prompts`,
					{
						method: 'POST',
						headers: {
							'content-type':
								'application/json',
						},
						body: JSON.stringify(
							Object.fromEntries(f),
						),
					},
				),
				b = await r.json();
			if (!r.ok)
				throw new Error(
					b.detail ?? 'Could not create prompt.',
				);
			const list = await fetch(
				`/api/projects/${project.id}/prompts`,
			).then(x => x.json());
			setPrompts(list.prompts);
			setCreateOpen(false);
			await inspect(b.prompt.id);
		} catch (e) {
			setError(
				e instanceof Error
					? e.message
					: 'Could not create prompt.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function addVersion(e: FormEvent<HTMLFormElement>) {
		e.preventDefault();
		if (!detail) return;
		setBusy(true);
		setError(null);
		const f = new FormData(e.currentTarget);
		try {
			const r = await fetch(
					`/api/projects/${project.id}/prompts/${detail.prompt.id}/versions`,
					{
						method: 'POST',
						headers: {
							'content-type':
								'application/json',
						},
						body: JSON.stringify(
							Object.fromEntries(f),
						),
					},
				),
				b = await r.json();
			if (!r.ok)
				throw new Error(
					b.detail ?? 'Could not create version.',
				);
			setVersionOpen(false);
			await inspect(detail.prompt.id);
		} catch (e) {
			setError(
				e instanceof Error
					? e.message
					: 'Could not create version.',
			);
		} finally {
			setBusy(false);
		}
	}
	async function archive() {
		if (!detail) return;
		setBusy(true);
		const r = await fetch(
			`/api/projects/${project.id}/prompts/${detail.prompt.id}`,
			{ method: 'DELETE' },
		);
		if (r.ok) {
			setPrompts(p =>
				p.map(x =>
					x.id === detail.prompt.id
						? { ...x, status: 'archived' }
						: x,
				),
			);
			setDetail(null);
		} else setError('Could not archive prompt.');
		setBusy(false);
	}
	function closeDetail() {
		setVersionOpen(false);
		setDetail(null);
	}
	return (
		<div className='prompt-page'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>
						AI applications
					</span>
					<h1>Prompts</h1>
					<p>
						Create reusable prompt templates
						with immutable version history.
					</p>
				</div>
				{canManage && (
					<button
						className='primary-action'
						onClick={() =>
							setCreateOpen(true)
						}>
						<Plus size={15} />
						Create prompt
					</button>
				)}
			</header>
			{error && (
				<div className='workspace-error'>{error}</div>
			)}
			<section className='catalog-table-panel'>
				<header>
					<div>
						<h2>Prompt registry</h2>
						<p>
							{prompts.length} prompts ·{' '}
							{prompts.filter(p => p.origin === 'preinstalled').length}{' '}
							preinstalled
						</p>
					</div>
					<label className='prompt-type-filter'>
						<ListFilter size={14} />
						<span>Type</span>
						<select
							value={typeFilter}
							onChange={event =>
								setTypeFilter(
									event.target.value as PromptTypeFilter,
								)
							}>
							<option value='all'>All types</option>
							<option value='system'>System</option>
							<option value='rag_answer'>RAG answer</option>
							<option value='evaluation'>Evaluation</option>
						</select>
					</label>
				</header>
				<div className='catalog-table-wrap'>
					<table>
						<thead>
							<tr>
								<th>Name</th>
								<th>Type</th>
								<th>Source</th>
								<th>
									Latest
									version
								</th>
								<th>
									Variables
								</th>
								<th>Status</th>
								<th>Updated</th>
								<th />
							</tr>
						</thead>
						<tbody>
							{visiblePrompts.map(p => (
								<tr
									key={
										p.id
									}
									onClick={() =>
										inspect(
											p.id,
										)
									}>
									<td>
										<span className='catalog-primary'>
											<FileCode2
												size={
													14
												}
											/>
											<strong>
												{
													p.name
												}
											</strong>
										</span>
									</td>
									<td>
										{p.prompt_type.replace(
											'_',
											' ',
										)}
									</td>
									<td>
										{p.origin === 'preinstalled'
											? 'Preinstalled'
											: 'Custom'}
									</td>
									<td>
										v
										{
											p.latest_version
										}
									</td>
									<td>
										{p
											.variables
											?.length
											? p.variables.join(
													', ',
												)
											: 'None'}
									</td>
									<td>
										<span
											className={`catalog-state ${p.status}`}>
											{
												p.status
											}
										</span>
									</td>
									<td>
										{formatDateTime(p.updated_at)}
									</td>
									<td>
										<ChevronRight
											size={
												14
											}
										/>
									</td>
								</tr>
							))}
						</tbody>
					</table>
					{!visiblePrompts.length && (
						<div className='mock-empty'>
							{typeFilter === 'all'
								? 'No prompts created yet.'
								: 'No prompts match this type.'}
						</div>
					)}
				</div>
			</section>
			{createOpen && (
				<PromptForm
					title='Create prompt'
					submit='Create prompt'
					busy={busy}
					onSubmit={create}
					onClose={() => setCreateOpen(false)}
				/>
			)}{' '}
			{detail && (
				<div className='index-detail-backdrop'>
					<section className='prompt-detail-panel'>
						<header>
							<div>
								<span className='eyebrow'>
									Prompt
								</span>
								<h2>
									{
										detail
											.prompt
											.name
									}
								</h2>
								<p>
									{detail.prompt.description ||
										'No description'}
								</p>
							</div>
							<button
									onClick={closeDetail}>
								<X size={18} />
							</button>
						</header>
						<div className='prompt-detail-actions'>
							<span className='catalog-state active'>
								{detail.prompt.origin === 'preinstalled'
									? 'Preinstalled'
									: 'Custom'}
							</span>
							{canManage &&
								detail.prompt
									.status ===
									'active' && (
									<>
										<button
											className='primary-action'
											onClick={() =>
												setVersionOpen(
													true,
												)
											}>
											<Plus
												size={
													14
												}
											/>
											New
											version
										</button>
										<button
											className='secondary-action'
											onClick={
												archive
											}>
											<Archive
												size={
													14
												}
											/>
											Archive
										</button>
									</>
								)}
						</div>
						<div className='prompt-version-list'>
							{detail.versions.map(
								v => (
									<article
										key={
											v.id
										}>
										<header>
											<strong>
												Version{' '}
												{
													v.version
												}
											</strong>
											<span>
												{formatDateTime(v.created_at)}
											</span>
										</header>
										<div className='prompt-variable-list'>
											{v.variables.map(
												x => (
													<code
														key={
															x
														}>{`{{${x}}}`}</code>
												),
											)}
										</div>
										<pre>
											{
												v.template
											}
										</pre>
										{v.change_note && (
											<p>
												{
													v.change_note
												}
											</p>
										)}
										<small>
											{
												v.content_sha256
											}
										</small>
									</article>
								),
							)}
						</div>
					</section>
				</div>
			)}
			{versionOpen && detail && (
				<PromptForm
					title='Create new version'
					submit='Create version'
					busy={busy}
					template={detail.versions[0]?.template}
					versionOnly
					onSubmit={addVersion}
					onClose={() => setVersionOpen(false)}
				/>
			)}
		</div>
	);
}
function PromptForm({
	title,
	submit,
	busy,
	onSubmit,
	onClose,
	template = '',
	versionOnly = false,
}: {
	title: string;
	submit: string;
	busy: boolean;
	onSubmit: (e: FormEvent<HTMLFormElement>) => void;
	onClose: () => void;
	template?: string;
	versionOnly?: boolean;
}) {
	return (
		<div
			className={`modal-backdrop${versionOnly ? ' prompt-version-backdrop' : ''}`}>
			<form
				className='workspace-modal prompt-form'
				onSubmit={onSubmit}>
				<div className='modal-title'>
					<h2>{title}</h2>
					<button
						type='button'
						className='icon-action'
						onClick={onClose}>
						<X size={18} />
					</button>
				</div>
				{!versionOnly && (
					<>
						<label>
							Name
							<input
								name='name'
								required
								maxLength={160}
							/>
						</label>
						<label>
							Purpose
							<input
								name='purpose'
								maxLength={500}
							/>
						</label>
						<label>
							Type
							<select
								name='prompt_type'
								defaultValue='rag_answer'>
								<option value='rag_answer'>
									RAG
									answer
								</option>
								<option value='system'>
									System
								</option>
								<option value='evaluation'>
									Evaluation
								</option>
							</select>
						</label>
						<label>
							Description
							<textarea
								name='description'
								rows={2}
							/>
						</label>
					</>
				)}
				<label>
					Template
					<textarea
						name='template'
						defaultValue={template}
						rows={12}
						required
						placeholder={
							'Use variables such as {{context}} and {{question}}'
						}
					/>
				</label>
				<label>
					Change note
					<input
						name='change_note'
						maxLength={500}
					/>
				</label>
				<div className='project-form-actions'>
					<button
						type='button'
						className='secondary-action'
						onClick={onClose}>
						Cancel
					</button>
					<button
						className='primary-action'
						disabled={busy}>
						{busy ? 'Saving…' : submit}
					</button>
				</div>
			</form>
		</div>
	);
}
