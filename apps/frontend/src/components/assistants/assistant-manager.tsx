'use client';

import { FormEvent, useState } from 'react';
import { Bot, ChevronRight, Plus, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { formatDateTime } from '@/lib/format';
import type { Assistant, Project } from '@/types/workspace';

export type AssistantCandidate = {
	variant_run_id: string;
	run_id: string;
	experiment_id: string;
	experiment_name: string;
	variant_id: string;
	variant_name: string;
	completed_at: string;
	aggregate_metrics: Record<string, number>;
};

export function AssistantManager({
	project,
	initialAssistants,
	candidates,
}: {
	project: Project;
	initialAssistants: Assistant[];
	candidates: AssistantCandidate[];
}) {
	const router = useRouter();
	const [assistants, setAssistants] = useState(initialAssistants);
	const [open, setOpen] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const canManage =
		project.role === 'owner' ||
		project.permissions?.assistants?.manage;

	async function create(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setBusy(true);
		setError(null);
		const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/assistants`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						name: form.get('name'),
						description:
							form.get('description'),
						experiment_variant_run_id:
							form.get(
								'variant_run_id',
							),
					}),
				},
			);
			const body = await response.json();
			if (!response.ok)
				throw new Error(
					typeof body.error === 'string'
						? body.error
						: body.error?.message ||
								'Could not create assistant.',
				);
			setAssistants(current => [body, ...current]);
			setOpen(false);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not create assistant.',
			);
		} finally {
			setBusy(false);
		}
	}

	return (
		<div className='catalog-page assistant-manager'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>
						AI applications
					</span>
					<h1>Assistants</h1>
					<p>
						Promote successful experiment
						variants into versioned RAG
						applications.
					</p>
				</div>
				{canManage && (
					<button
						className='primary-action'
						disabled={!candidates.length}
						onClick={() => setOpen(true)}>
						<Plus size={15} />
						Create assistant
					</button>
				)}
			</header>
			{error && (
				<div className='workspace-error' role='alert'>
					{error}
				</div>
			)}
			<section className='catalog-table-panel'>
				<header>
					<div>
						<h2>Assistant registry</h2>
						<p>
							{assistants.length}{' '}
							assistants
						</p>
					</div>
				</header>
				<div className='catalog-table-wrap'>
					<table>
						<thead>
							<tr>
								<th>
									Assistant
								</th>
								<th>
									Revision
								</th>
								<th>
									Experiment
								</th>
								<th>Variant</th>
								<th>Status</th>
								<th />
							</tr>
						</thead>
						<tbody>
							{assistants.map(
								assistant => (
									<tr
										key={
											assistant.id
										}
										onClick={() =>
											router.push(
												`/projects/${project.id}/assistants/${assistant.id}`,
											)
										}>
										<td>
											<span className='catalog-primary'>
												<Bot
													size={
														14
													}
												/>
												<strong>
													{
														assistant.name
													}
												</strong>
											</span>
										</td>
										<td>
											{assistant.active_revision_version
												? `v${assistant.active_revision_version}`
												: '—'}
										</td>
										<td>
											{assistant.source_experiment_name ||
												'—'}
										</td>
										<td>
											{assistant.source_variant_name ||
												'—'}
										</td>
										<td>
											<span
												className={`catalog-state ${assistant.status}`}>
												{
													assistant.status
												}
											</span>
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
					{!assistants.length && (
						<div className='mock-empty'>
							{candidates.length
								? 'Create an assistant from a completed experiment run.'
								: 'Complete an experiment variant run before creating an assistant.'}
						</div>
					)}
				</div>
			</section>
			{open && (
				<div className='modal-backdrop'>
					<form
						className='workspace-modal assistant-create-form'
						onSubmit={create}>
						<div className='modal-title'>
							<div>
								<h2>
									Create
									assistant
								</h2>
								<p className='modal-copy'>
									The
									selected
									run
									becomes
									immutable
									assistant
									revision
									v1.
								</p>
							</div>
							<button
								type='button'
								className='icon-action'
								onClick={() =>
									setOpen(
										false,
									)
								}>
								<X size={18} />
							</button>
						</div>
						<label>
							Name
							<input
								name='name'
								required
								maxLength={160}
							/>
						</label>
						<label>
							Description
							<textarea
								name='description'
								rows={3}
								maxLength={2000}
							/>
						</label>
						<label>
							Completed experiment run
							<select
								name='variant_run_id'
								required
								defaultValue=''>
								<option
									value=''
									disabled>
									Select a
									successful
									variant
								</option>
								{candidates.map(
									candidate => (
										<option
											key={
												candidate.variant_run_id
											}
											value={
												candidate.variant_run_id
											}>
											{
												candidate.experiment_name
											}{' '}
											·{' '}
											{
												candidate.variant_name
											}{' '}
											·{' '}
											{formatDateTime(
												candidate.completed_at,
											)}
										</option>
									),
								)}
							</select>
						</label>
						<p className='assistant-run-note'>
							The index, prompt
							versions, retrieval
							settings, generation
							settings, and
							configuration hash will
							be copied from this run.
						</p>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={() =>
									setOpen(
										false,
									)
								}>
								Cancel
							</button>
							<button
								className='primary-action'
								disabled={busy}>
								{busy
									? 'Creating…'
									: 'Create assistant'}
							</button>
						</div>
					</form>
				</div>
			)}
		</div>
	);
}
