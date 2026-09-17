'use client';

import { FormEvent, useState } from 'react';
import { ChevronRight, ClipboardCheck, Plus, Trash2, X } from 'lucide-react';
import type {
	BenchmarkCase,
	BenchmarkDataset,
	BenchmarkVersion,
	Project,
} from '@/types/workspace';
import { formatDateTime } from '@/lib/format';

export type BenchmarkDetail = {
	dataset: BenchmarkDataset & { content: BenchmarkCase[] };
	versions: BenchmarkVersion[];
};
type EditableCase = Omit<BenchmarkCase, 'case_id'> & { case_id?: string };

const emptyCase = (): EditableCase => ({
	question: '',
	reference_answer: '',
	expected_context: '',
	tags: [],
});

export function BenchmarkManager({
	project,
	initialDatasets,
	initialDetail = null,
}: {
	project: Project;
	initialDatasets: BenchmarkDataset[];
	initialDetail?: BenchmarkDetail | null;
}) {
	const [datasets, setDatasets] = useState(initialDatasets);
	const [detail, setDetail] = useState<BenchmarkDetail | null>(
		initialDetail,
	);
	const [createOpen, setCreateOpen] = useState(false);
	const [versionOpen, setVersionOpen] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const canManage =
		project.role === 'owner' ||
		project.permissions?.benchmarks?.manage;

	async function loadDatasets() {
		const response = await fetch(
			`/api/projects/${project.id}/benchmarks`,
		);
		const body = await response.json();
		if (!response.ok)
			throw new Error(
				body.error?.message ??
					'Could not load benchmarks.',
			);
		setDatasets(body.datasets);
	}

	async function inspect(datasetId: string) {
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/benchmarks/${datasetId}`,
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body.error?.message ??
						'Could not load benchmark.',
				);
			setDetail(body);
		} catch (caught) {
			setError(message(caught));
		} finally {
			setBusy(false);
		}
	}

	async function createDataset(payload: BenchmarkFormPayload) {
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/benchmarks`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify(payload),
				},
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body.error?.message ??
						'Could not create benchmark.',
				);
			await loadDatasets();
			setCreateOpen(false);
			await inspect(body.id);
		} catch (caught) {
			setError(message(caught));
		} finally {
			setBusy(false);
		}
	}

	async function createVersion(payload: BenchmarkFormPayload) {
		if (!detail) return;
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/benchmarks/${detail.dataset.id}/versions`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						description:
							payload.description,
						cases: payload.cases,
					}),
				},
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					body.error?.message ??
						'Could not create dataset version.',
				);
			await loadDatasets();
			setVersionOpen(false);
			await inspect(body.id);
		} catch (caught) {
			setError(message(caught));
		} finally {
			setBusy(false);
		}
	}

	function closeDetail() {
		setVersionOpen(false);
		setDetail(null);
	}

	return (
		<div className='benchmark-page'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>
						Development
					</span>
					<h1>Benchmarks</h1>
					<p>
						Versioned test datasets for
						repeatable experiment
						evaluation.
					</p>
				</div>
				{canManage && (
					<button
						className='primary-action'
						onClick={() =>
							setCreateOpen(true)
						}>
						<Plus size={15} />
						Create dataset
					</button>
				)}
			</header>
			{error && (
				<div className='workspace-error'>{error}</div>
			)}
			<section className='catalog-table-panel'>
				<header>
					<div>
						<h2>Dataset registry</h2>
						<p>
							{datasets.length}{' '}
							benchmark datasets
						</p>
					</div>
				</header>
				<div className='catalog-table-wrap'>
					<table>
						<thead>
							<tr>
								<th>Dataset</th>
								<th>
									Latest
									version
								</th>
								<th>
									Test
									cases
								</th>
								<th>
									Versions
								</th>
								<th>Created</th>
								<th />
							</tr>
						</thead>
						<tbody>
							{datasets.map(
								dataset => (
									<tr
										key={
											dataset.id
										}
										onClick={() =>
											inspect(
												dataset.id,
											)
										}>
										<td>
											<span className='catalog-primary'>
												<ClipboardCheck
													size={
														14
													}
												/>
												<strong>
													{
														dataset.name
													}
												</strong>
											</span>
										</td>
										<td>
											v
											{
												dataset.version
											}
										</td>
										<td>
											{
												dataset.example_count
											}
										</td>
										<td>
											{
												dataset.version_count
											}
										</td>
										<td>
											{formatDateTime(
												dataset.created_at,
											)}
										</td>
										<td>
											<ChevronRight
												size={
													14
												}
											/>
										</td>
									</tr>
								),
							)}
						</tbody>
					</table>
					{!datasets.length && (
						<div className='mock-empty'>
							No benchmark datasets
							yet.
						</div>
					)}
				</div>
			</section>
			{createOpen && (
				<BenchmarkForm
					title='Create benchmark dataset'
					submitLabel='Create dataset'
					busy={busy}
					onSubmit={createDataset}
					onClose={() => setCreateOpen(false)}
				/>
			)}
			{detail && (
				<div className='index-detail-backdrop'>
					<section className='benchmark-detail-panel'>
						<header>
							<div>
								<span className='eyebrow'>
									Benchmark
									dataset
								</span>
								<h2>
									{
										detail
											.dataset
											.name
									}
								</h2>
								<p>
									{detail
										.dataset
										.description ||
										'No description'}
								</p>
							</div>
							<button
								onClick={
									closeDetail
								}
								aria-label='Close details'>
								<X size={18} />
							</button>
						</header>
						<div className='benchmark-detail-actions'>
							<span className='catalog-state active'>
								Version{' '}
								{
									detail
										.dataset
										.version
								}
							</span>
							<span>
								{
									detail
										.dataset
										.content
										.length
								}{' '}
								test cases
							</span>
							{canManage && (
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
							)}
						</div>
						<div className='benchmark-detail-content'>
							<section className='benchmark-version-strip'>
								<strong>
									Version
									history
								</strong>
								<div>
									{detail.versions.map(
										version => (
											<button
												key={
													version.id
												}
												className={
													version.id ===
													detail
														.dataset
														.id
														? 'selected'
														: ''
												}
												onClick={() =>
													inspect(
														version.id,
													)
												}>
												v
												{
													version.version
												}
											</button>
										),
									)}
								</div>
							</section>
							<div className='benchmark-case-table'>
								<table>
									<thead>
										<tr>
											<th>
												#
											</th>
											<th>
												Question
											</th>
											<th>
												Reference
												answer
											</th>
											<th>
												Tags
											</th>
										</tr>
									</thead>
									<tbody>
										{detail.dataset.content.map(
											(
												item,
												index,
											) => (
												<tr
													key={
														item.case_id
													}>
													<td>
														{index +
															1}
													</td>
													<td>
														{
															item.question
														}
													</td>
													<td>
														{item.reference_answer ||
															'—'}
													</td>
													<td>
														{item.tags.join(
															', ',
														) ||
															'—'}
													</td>
												</tr>
											),
										)}
									</tbody>
								</table>
							</div>
							<small className='benchmark-hash'>
								SHA-256 ·{' '}
								{
									detail
										.dataset
										.content_sha256
								}
							</small>
						</div>
					</section>
				</div>
			)}
			{versionOpen && detail && (
				<BenchmarkForm
					title={`Create ${detail.dataset.name} v${detail.dataset.version + 1}`}
					submitLabel='Create version'
					busy={busy}
					initialDescription={
						detail.dataset.description ?? ''
					}
					initialCases={detail.dataset.content}
					versionOnly
					onSubmit={createVersion}
					onClose={() => setVersionOpen(false)}
				/>
			)}
		</div>
	);
}

type BenchmarkFormPayload = {
	name?: string;
	description: string;
	cases: EditableCase[];
};

function BenchmarkForm({
	title,
	submitLabel,
	busy,
	onSubmit,
	onClose,
	initialDescription = '',
	initialCases,
	versionOnly = false,
}: {
	title: string;
	submitLabel: string;
	busy: boolean;
	onSubmit: (payload: BenchmarkFormPayload) => void;
	onClose: () => void;
	initialDescription?: string;
	initialCases?: BenchmarkCase[];
	versionOnly?: boolean;
}) {
	const [cases, setCases] = useState<EditableCase[]>(
		initialCases?.map(item => ({ ...item })) ?? [emptyCase()],
	);

	function updateCase(index: number, patch: Partial<EditableCase>) {
		setCases(current =>
			current.map((item, position) =>
				position === index
					? { ...item, ...patch }
					: item,
			),
		);
	}

	function submit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const form = new FormData(event.currentTarget);
		onSubmit({
			name: versionOnly
				? undefined
				: String(form.get('name') ?? ''),
			description: String(form.get('description') ?? ''),
			cases: cases.map(item => ({
				...item,
				reference_answer: item.reference_answer || null,
				expected_context: item.expected_context || null,
			})),
		});
	}

	return (
		<div className='modal-backdrop benchmark-form-backdrop'>
			<form
				className='workspace-modal benchmark-form'
				onSubmit={submit}>
				<div className='modal-title'>
					<div>
						<h2>{title}</h2>
						<p className='modal-copy'>
							Each version is stored
							as an immutable
							snapshot.
						</p>
					</div>
					<button
						type='button'
						className='icon-action'
						onClick={onClose}>
						<X size={18} />
					</button>
				</div>
				{!versionOnly && (
					<label>
						Dataset name
						<input
							name='name'
							required
							maxLength={160}
						/>
					</label>
				)}
				<label>
					Description
					<textarea
						name='description'
						defaultValue={
							initialDescription
						}
						rows={2}
						maxLength={2000}
					/>
				</label>
				<div className='benchmark-case-editor'>
					<header>
						<div>
							<strong>
								Test cases
							</strong>
							<span>
								{cases.length}{' '}
								cases
							</span>
						</div>
						<button
							type='button'
							className='secondary-action'
							onClick={() =>
								setCases(
									current => [
										...current,
										emptyCase(),
									],
								)
							}>
							<Plus size={13} /> Add
							case
						</button>
					</header>
					{cases.map((item, index) => (
						<article
							key={
								item.case_id ??
								index
							}>
							<header>
								<strong>
									Case{' '}
									{index +
										1}
								</strong>
								{cases.length >
									1 && (
									<button
										type='button'
										onClick={() =>
											setCases(
												current =>
													current.filter(
														(
															_,
															position,
														) =>
															position !==
															index,
													),
											)
										}
										aria-label={`Remove case ${index + 1}`}>
										<Trash2
											size={
												14
											}
										/>
									</button>
								)}
							</header>
							<label>
								Question
								<textarea
									value={
										item.question
									}
									onChange={event =>
										updateCase(
											index,
											{
												question: event
													.target
													.value,
											},
										)
									}
									required
									rows={2}
								/>
							</label>
							<label>
								Reference answer
								<textarea
									value={
										item.reference_answer ??
										''
									}
									onChange={event =>
										updateCase(
											index,
											{
												reference_answer:
													event
														.target
														.value,
											},
										)
									}
									rows={2}
								/>
							</label>
							<label>
								Expected context
								<textarea
									value={
										item.expected_context ??
										''
									}
									onChange={event =>
										updateCase(
											index,
											{
												expected_context:
													event
														.target
														.value,
											},
										)
									}
									rows={2}
								/>
							</label>
							<label>
								Tags
								<input
									value={item.tags.join(
										', ',
									)}
									onChange={event =>
										updateCase(
											index,
											{
												tags: event.target.value
													.split(
														',',
													)
													.map(
														tag =>
															tag.trim(),
													)
													.filter(
														Boolean,
													),
											},
										)
									}
									placeholder='policy, difficult'
								/>
							</label>
						</article>
					))}
				</div>
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
						{busy ? 'Saving…' : submitLabel}
					</button>
				</div>
			</form>
		</div>
	);
}

function message(error: unknown) {
	return error instanceof Error ? error.message : 'Something went wrong.';
}
