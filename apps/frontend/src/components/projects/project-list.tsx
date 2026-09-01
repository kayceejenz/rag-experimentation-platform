'use client';

import { FormEvent, useState } from 'react';
import { ChevronRight, Folder, Pencil, Plus, Trash2, X } from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type { Project } from '@/types/workspace';

async function createProject(body: {
	name: string;
	description: string | null;
}) {
	const response = await fetch('/api/projects', {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(body),
	});
	const result = (await response.json().catch(() => ({}))) as Project & {
		error?: string | { message?: string };
		detail?: string;
	};
	if (!response.ok)
		throw new Error(
			(typeof result.error === 'string'
				? result.error
				: result.error?.message) ??
				result.detail ??
				'Could not create project.',
		);
	return result;
}

export function ProjectList({
	initialProjects,
}: {
	initialProjects: Project[];
}) {
	const [projects, setProjects] = useState(initialProjects);
	const [showCreate, setShowCreate] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [renameTarget, setRenameTarget] = useState<Project | null>(null);
	const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);

	async function submit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setBusy(true);
		setError(null);
		const form = new FormData(event.currentTarget);
		try {
			const project = await createProject({
				name: String(form.get('name')),
				description:
					String(form.get('description') || '') ||
					null,
			});
			setProjects(current => [...current, project]);
			setShowCreate(false);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not create project.',
			);
		} finally {
			setBusy(false);
		}
	}

	async function rename(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		if (!renameTarget) return;
		setBusy(true);
		setError(null);
		const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(
				`/api/projects/${renameTarget.id}`,
				{
					method: 'PATCH',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						name: form.get('name'),
					}),
				},
			);
			const result = (await response
				.json()
				.catch(() => ({}))) as Project & {
				error?: string | { message?: string };
				detail?: string;
			};
			if (!response.ok)
				throw new Error(
					(typeof result.error === 'string'
						? result.error
						: result.error?.message) ??
						result.detail ??
						'Could not rename project.',
				);
			setProjects(current =>
				current.map(project =>
					project.id === result.id
						? result
						: project,
				),
			);
			setRenameTarget(null);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not rename project.',
			);
		} finally {
			setBusy(false);
		}
	}

	async function removeProject() {
		if (!deleteTarget || deleteTarget.is_default) return;
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${deleteTarget.id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok) {
				const result = await response
					.json()
					.catch(() => ({}));
				throw new Error(
					result?.error?.message ??
						result?.detail ??
						'Could not delete project.',
				);
			}
			setProjects(current =>
				current.filter(
					project =>
						project.id !== deleteTarget.id,
				),
			);
			setDeleteTarget(null);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not delete project.',
			);
		} finally {
			setBusy(false);
		}
	}

	return (
		<div className='projects-page'>
			<header className='projects-page-header'>
				<div>
					<h1>Projects</h1>
					<p>
						Organize knowledge and AI work
						into separate project spaces.
					</p>
				</div>
				<button
					className='primary-action'
					onClick={() => setShowCreate(true)}>
					<Plus size={15} />
					New project
				</button>
			</header>
			{error && (
				<div className='workspace-error'>{error}</div>
			)}
			<div className='simple-project-list'>
				{projects.map(project => (
					<div
						className='simple-project-row'
						key={project.id}>
						<SmoothLink
							href={`/projects/${project.id}`}>
							<span className='simple-project-icon'>
								<Folder
									size={
										17
									}
								/>
							</span>
							<span className='simple-project-copy'>
								<strong>
									{
										project.name
									}
								</strong>
								{project.description && (
									<small>
										{
											project.description
										}
									</small>
								)}
							</span>
							{project.is_default && (
								<span className='default-project-badge'>
									Default
								</span>
							)}
							<ChevronRight
								size={16}
							/>
						</SmoothLink>
						<div className='project-row-actions'>
							<button
								onClick={() =>
									setRenameTarget(
										project,
									)
								}
								aria-label={`Rename ${project.name}`}
								title='Rename'>
								<Pencil
									size={
										14
									}
								/>
							</button>
							<button
								onClick={() =>
									setDeleteTarget(
										project,
									)
								}
								disabled={
									project.is_default
								}
								aria-label={`Delete ${project.name}`}
								title={
									project.is_default
										? 'The default project cannot be deleted'
										: 'Delete'
								}>
								<Trash2
									size={
										14
									}
								/>
							</button>
						</div>
					</div>
				))}
			</div>
			{showCreate && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'>
					<form
						className='workspace-modal bot-create-modal'
						onSubmit={submit}>
						<div className='modal-title'>
							<div>
								<h2>
									Create
									project
								</h2>
								<p>
									Add a
									project
									to this
									workspace.
								</p>
							</div>
							<button
								type='button'
								className='icon-action'
								onClick={() =>
									setShowCreate(
										false,
									)
								}
								aria-label='Close'>
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
										160
									}
									autoFocus
								/>
							</label>
							<label>
								Description{' '}
								<small>
									Optional
								</small>
								<textarea
									name='description'
									rows={3}
									maxLength={
										2000
									}
								/>
							</label>
						</div>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={() =>
									setShowCreate(
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
									: 'Create'}
							</button>
						</div>
					</form>
				</div>
			)}
			{renameTarget && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'>
					<form
						className='workspace-modal project-action-modal'
						onSubmit={rename}>
						<div className='modal-title'>
							<div>
								<h2>
									Rename
									project
								</h2>
								<p>
									Update
									the
									project
									name
									everywhere
									in the
									workspace.
								</p>
							</div>
							<button
								type='button'
								className='icon-action'
								onClick={() =>
									setRenameTarget(
										null,
									)
								}
								aria-label='Close'>
								<X size={18} />
							</button>
						</div>
						<label>
							Project name
							<input
								name='name'
								defaultValue={
									renameTarget.name
								}
								required
								minLength={2}
								maxLength={160}
								autoFocus
							/>
						</label>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={() =>
									setRenameTarget(
										null,
									)
								}>
								Cancel
							</button>
							<button
								className='primary-action'
								disabled={busy}>
								{busy
									? 'Saving…'
									: 'Save name'}
							</button>
						</div>
					</form>
				</div>
			)}
			{deleteTarget && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'>
					<section className='workspace-modal project-action-modal'>
						<div className='modal-title'>
							<div>
								<h2>
									Delete
									project?
								</h2>
								<p>
									This
									will
									remove{' '}
									<strong>
										{
											deleteTarget.name
										}
									</strong>{' '}
									and its
									project-scoped
									resources.
								</p>
							</div>
							<button
								className='icon-action'
								onClick={() =>
									setDeleteTarget(
										null,
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
									setDeleteTarget(
										null,
									)
								}>
								Cancel
							</button>
							<button
								className='danger-action'
								onClick={
									removeProject
								}
								disabled={busy}>
								{busy
									? 'Deleting…'
									: 'Delete project'}
							</button>
						</div>
					</section>
				</div>
			)}
		</div>
	);
}
