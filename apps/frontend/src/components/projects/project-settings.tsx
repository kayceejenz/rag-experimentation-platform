'use client';

import { FormEvent, useState } from 'react';
import { Check, Copy, Plus, Shield, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import type {
	FeaturePermission,
	Project,
	ProjectFeature,
	ProjectMember,
} from '@/types/workspace';

const features: Array<{
	id: ProjectFeature;
	label: string;
	description: string;
}> = [
	{
		id: 'knowledge',
		label: 'Knowledge Base',
		description: 'Documents, folders, and ingestion',
	},
	{
		id: 'indexes',
		label: 'Indexes',
		description: 'Index configurations and builds',
	},
	{
		id: 'experiments',
		label: 'Experiments',
		description: 'Experimental configurations and comparisons',
	},
	{
		id: 'benchmarks',
		label: 'Benchmarks',
		description: 'Evaluation datasets and benchmarks',
	},
	{
		id: 'prompts',
		label: 'Prompts',
		description: 'Prompt templates and immutable versions',
	},
	{
		id: 'assistants',
		label: 'Assistants',
		description: 'Assistants and their revisions',
	},
	{
		id: 'runs',
		label: 'Runs',
		description: 'Execution history, lineage, and traces',
	},
	{
		id: 'settings',
		label: 'Settings',
		description: 'Project configuration',
	},
];

function defaultPermissions(): Record<ProjectFeature, FeaturePermission> {
	return Object.fromEntries(
		features.map(feature => [
			feature.id,
			{ view: true, manage: false },
		]),
	) as Record<ProjectFeature, FeaturePermission>;
}

export function ProjectSettings({
	project,
	initialMembers,
	currentUserId,
}: {
	project: Project;
	initialMembers: ProjectMember[];
	currentUserId: string;
}) {
	const router = useRouter();
	const [members, setMembers] = useState(initialMembers);
	const [selectedId, setSelectedId] = useState(
		initialMembers[0]?.user_id ?? null,
	);
	const [addOpen, setAddOpen] = useState(false);
	const [draft, setDraft] = useState(defaultPermissions());
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [notice, setNotice] = useState<string | null>(null);
	const currentMember = members.find(
		member => member.user_id === currentUserId,
	);
	const canEditGeneral =
		project.role === 'owner' ||
		Boolean(currentMember?.permissions.settings.manage);
	const isOwner = project.role === 'owner';
	const selected =
		members.find(member => member.user_id === selectedId) ?? null;

	async function reloadMembers() {
		const response = await fetch(
			`/api/projects/${project.id}/members`,
		);
		if (response.ok) setMembers((await response.json()).members);
	}

	async function saveGeneral(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setBusy(true);
		setError(null);
		setNotice(null);
		const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(
				`/api/projects/${project.id}`,
				{
					method: 'PATCH',
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
			const body = await response.json().catch(() => ({}));
			if (!response.ok)
				throw new Error(
					body?.detail ??
						'Could not update project.',
				);
			setNotice('Project details updated.');
			router.refresh();
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not update project.',
			);
		} finally {
			setBusy(false);
		}
	}

	async function addMember(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setBusy(true);
		setError(null);
		setNotice(null);
		const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/members`,
				{
					method: 'POST',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						email: form.get('email'),
						permissions: draft,
					}),
				},
			);
			const body = await response.json().catch(() => ({}));
			if (!response.ok)
				throw new Error(
					body?.detail ?? 'Could not add member.',
				);
			await reloadMembers();
			setAddOpen(false);
			setDraft(defaultPermissions());
			setNotice('Member added.');
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not add member.',
			);
		} finally {
			setBusy(false);
		}
	}

	async function saveAccess() {
		if (!selected || selected.role === 'owner') return;
		setBusy(true);
		setError(null);
		setNotice(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/members/${selected.user_id}`,
				{
					method: 'PUT',
					headers: {
						'content-type':
							'application/json',
					},
					body: JSON.stringify({
						permissions:
							selected.permissions,
					}),
				},
			);
			const body = await response.json().catch(() => ({}));
			if (!response.ok)
				throw new Error(
					body?.detail ??
						'Could not update access.',
				);
			setNotice('Member access updated.');
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not update access.',
			);
		} finally {
			setBusy(false);
		}
	}

	async function removeMember() {
		if (!selected || selected.role === 'owner') return;
		setBusy(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/members/${selected.user_id}`,
				{ method: 'DELETE' },
			);
			if (!response.ok) {
				const body = await response
					.json()
					.catch(() => ({}));
				throw new Error(
					body?.detail ??
						'Could not remove member.',
				);
			}
			const remaining = members.filter(
				member => member.user_id !== selected.user_id,
			);
			setMembers(remaining);
			setSelectedId(remaining[0]?.user_id ?? null);
			setNotice('Member removed.');
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not remove member.',
			);
		} finally {
			setBusy(false);
		}
	}

	function updatePermission(
		feature: ProjectFeature,
		action: 'view' | 'manage',
		checked: boolean,
		target: 'draft' | 'selected',
	) {
		const update = (
			permissions: Record<ProjectFeature, FeaturePermission>,
		) => ({
			...permissions,
			[feature]: {
				view:
					action === 'manage' && checked
						? true
						: action === 'view'
							? checked
							: permissions[feature]
									.view,
				manage:
					action === 'view' && !checked
						? false
						: action === 'manage'
							? checked
							: permissions[feature]
									.manage,
			},
		});
		if (target === 'draft') setDraft(update);
		else if (selected)
			setMembers(current =>
				current.map(member =>
					member.user_id === selected.user_id
						? {
								...member,
								permissions:
									update(
										member.permissions,
									),
							}
						: member,
				),
			);
	}

	return (
		<div className='project-settings-page'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>
						Settings
					</span>
					<h1>Project settings</h1>
					<p>
						Manage project identity and
						feature-level access.
					</p>
				</div>
			</header>
			{error && (
				<div className='workspace-error'>{error}</div>
			)}
			{notice && (
				<div className='workspace-notice'>{notice}</div>
			)}
			<section className='settings-section'>
				<header>
					<div>
						<h2>General</h2>
						<p>
							Basic information used
							across the workspace.
						</p>
					</div>
				</header>
				<form
					onSubmit={saveGeneral}
					className='settings-general-form'>
					<label>
						Project name
						<input
							name='name'
							defaultValue={
								project.name
							}
							required
							maxLength={160}
							disabled={
								!canEditGeneral
							}
						/>
					</label>
					<label>
						Project description
						<textarea
							name='description'
							defaultValue={
								project.description ??
								''
							}
							maxLength={2000}
							rows={3}
							disabled={
								!canEditGeneral
							}
						/>
					</label>
					<label>
						Project ID
						<div className='settings-copy-field'>
							<code>
								{project.id}
							</code>
							<button
								type='button'
								onClick={() =>
									navigator.clipboard.writeText(
										project.id,
									)
								}
								aria-label='Copy project ID'>
								<Copy
									size={
										14
									}
								/>
							</button>
						</div>
					</label>
					{canEditGeneral && (
						<button
							className='primary-action'
							disabled={busy}>
							{busy
								? 'Saving…'
								: 'Save changes'}
						</button>
					)}
				</form>
			</section>
			<section className='settings-section'>
				<header>
					<div>
						<h2>Members and access</h2>
						<p>
							Access is granted
							independently for each
							project feature.
						</p>
					</div>
					{isOwner && (
						<button
							className='secondary-action'
							onClick={() => {
								setAddOpen(
									true,
								);
								setDraft(
									defaultPermissions(),
								);
							}}>
							<Plus size={14} />
							Add member
						</button>
					)}
				</header>
				<div className='settings-access-layout'>
					<div className='settings-member-list'>
						{members.map(member => (
							<button
								key={
									member.user_id
								}
								className={
									selectedId ===
									member.user_id
										? 'active'
										: ''
								}
								onClick={() =>
									setSelectedId(
										member.user_id,
									)
								}>
								<span>
									{(
										member.display_name ??
										member.email
									)
										.slice(
											0,
											1,
										)
										.toUpperCase()}
								</span>
								<div>
									<strong>
										{member.display_name ??
											member.email}
									</strong>
									<small>
										{
											member.email
										}
									</small>
								</div>
								{member.role ===
									'owner' && (
									<em>
										Owner
									</em>
								)}
							</button>
						))}
					</div>
					{selected && (
						<div className='settings-permission-panel'>
							<header>
								<div>
									<Shield
										size={
											16
										}
									/>
									<span>
										<strong>
											{selected.display_name ??
												selected.email}
										</strong>
										<small>
											{selected.role ===
											'owner'
												? 'Owner · all privileges'
												: 'Feature access'}
										</small>
									</span>
								</div>
								{isOwner &&
									selected.role !==
										'owner' && (
										<button
											className='settings-remove-member'
											onClick={
												removeMember
											}
											disabled={
												busy
											}>
											<Trash2
												size={
													14
												}
											/>
											Remove
										</button>
									)}
							</header>
							<PermissionMatrix
								permissions={
									selected.permissions
								}
								disabled={
									!isOwner ||
									selected.role ===
										'owner'
								}
								onChange={(
									feature,
									action,
									checked,
								) =>
									updatePermission(
										feature,
										action,
										checked,
										'selected',
									)
								}
							/>
							{isOwner &&
								selected.role !==
									'owner' && (
									<footer>
										<button
											className='primary-action'
											onClick={
												saveAccess
											}
											disabled={
												busy
											}>
											{busy
												? 'Saving…'
												: 'Save access'}
										</button>
									</footer>
								)}
						</div>
					)}
				</div>
			</section>
			{addOpen && (
				<div
					className='modal-backdrop'
					role='dialog'
					aria-modal='true'>
					<form
						className='workspace-modal settings-add-member'
						onSubmit={addMember}>
						<div className='modal-title'>
							<div>
								<h2>
									Add
									project
									member
								</h2>
								<p>
									The
									account
									must
									already
									be
									registered.
								</p>
							</div>
						</div>
						<label>
							Email address
							<input
								name='email'
								type='email'
								required
								autoFocus
							/>
						</label>
						<PermissionMatrix
							permissions={draft}
							disabled={false}
							onChange={(
								feature,
								action,
								checked,
							) =>
								updatePermission(
									feature,
									action,
									checked,
									'draft',
								)
							}
						/>
						<div className='project-form-actions'>
							<button
								type='button'
								className='secondary-action'
								onClick={() =>
									setAddOpen(
										false,
									)
								}>
								Cancel
							</button>
							<button
								className='primary-action'
								disabled={busy}>
								{busy
									? 'Adding…'
									: 'Add member'}
							</button>
						</div>
					</form>
				</div>
			)}
		</div>
	);
}

function PermissionMatrix({
	permissions,
	disabled,
	onChange,
}: {
	permissions: Record<ProjectFeature, FeaturePermission>;
	disabled: boolean;
	onChange: (
		feature: ProjectFeature,
		action: 'view' | 'manage',
		checked: boolean,
	) => void;
}) {
	return (
		<div className='permission-matrix'>
			<div className='permission-heading'>
				<span>Feature</span>
				<span>View</span>
				<span>Manage</span>
			</div>
			{features.map(feature => (
				<div
					className='permission-row'
					key={feature.id}>
					<span>
						<strong>{feature.label}</strong>
						<small>
							{feature.description}
						</small>
					</span>
					{(['view', 'manage'] as const).map(
						action => (
							<label key={action}>
								<input
									type='checkbox'
									checked={
										permissions[
											feature
												.id
										][
											action
										]
									}
									disabled={
										disabled
									}
									onChange={event =>
										onChange(
											feature.id,
											action,
											event
												.target
												.checked,
										)
									}
								/>
								<span>
									<Check
										size={
											12
										}
									/>
								</span>
							</label>
						),
					)}
				</div>
			))}
		</div>
	);
}
