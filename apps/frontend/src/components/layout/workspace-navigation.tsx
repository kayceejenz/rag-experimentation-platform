'use client';

import { usePathname, useRouter } from 'next/navigation';
import {
	Bot,
	ChevronDown,
	Database,
	FlaskConical,
	FolderKanban,
	Gauge,
	Home,
	Layers3,
	PlayCircle,
	Settings,
} from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type { Project } from '@/types/workspace';

const groups = [
	{
		label: 'Data',
		items: [
			{
				label: 'Knowledge Base',
				slug: 'knowledge',
				icon: Database,
			},
			{ label: 'Indexes', slug: 'indexes', icon: Layers3 },
		],
	},
	{
		label: 'Development',
		items: [
			{
				label: 'Experiments',
				slug: 'experiments',
				icon: FlaskConical,
			},
			{
				label: 'Benchmarks',
				slug: 'benchmarks',
				icon: Gauge,
			},
		],
	},
	{
		label: 'AI applications',
		items: [{ label: 'Assistants', slug: 'assistants', icon: Bot }],
	},
	{
		label: 'Operations',
		items: [{ label: 'Runs', slug: 'runs', icon: PlayCircle }],
	},
];

export function WorkspaceNavigation({
	projects,
	activeProjectId,
	compact = false,
}: {
	projects: Project[];
	activeProjectId?: string | null;
	compact?: boolean;
}) {
	const pathname = usePathname();
	const router = useRouter();
	const resolvedProjectId =
		activeProjectId ??
		projects.find(project => project.is_default)?.id ??
		projects[0]?.id;
	const activeProject = projects.find(
		project => project.id === resolvedProjectId,
	);
	return (
		<nav
			className={
				compact
					? 'structured-nav compact'
					: 'structured-nav'
			}
			aria-label='Workspace navigation'>
			<div className='nav-group'>
				<span className='nav-group-label'>
					Workspace
				</span>
				<SmoothLink
					href='/'
					className={
						pathname === '/' ? 'active' : ''
					}>
					<Home size={16} />
					<span>Overview</span>
				</SmoothLink>
				<SmoothLink
					href='/projects'
					className={
						pathname === '/projects'
							? 'active'
							: ''
					}>
					<FolderKanban size={16} />
					<span>Projects</span>
				</SmoothLink>
			</div>
			{activeProject && (
				<div className='nav-project-picker'>
					<label
						htmlFor={
							compact
								? 'mobile-project-picker'
								: 'project-picker'
						}>
						Project context
					</label>
					<div className='project-context-switcher'>
						<span className='project-switcher-icon'>
							{activeProject.name
								.slice(0, 1)
								.toUpperCase()}
						</span>
						<span className='project-switcher-copy'>
							<small>
								{activeProject.is_default
									? 'Default project'
									: 'Current project'}
							</small>
							<strong>
								{
									activeProject.name
								}
							</strong>
						</span>
						<ChevronDown size={15} />
						<select
							aria-label='Switch project'
							id={
								compact
									? 'mobile-project-picker'
									: 'project-picker'
							}
							value={activeProject.id}
							onChange={event =>
								router.push(
									`/projects/${event.target.value}`,
								)
							}>
							{projects.map(
								project => (
									<option
										value={
											project.id
										}
										key={
											project.id
										}>
										{
											project.name
										}
										{project.is_default
											? ' — Default'
											: ''}
									</option>
								),
							)}
						</select>
					</div>
				</div>
			)}
			{activeProject && (
				<div className='nav-project-context'>
					{groups.map(group => (
						<div
							className='nav-group'
							key={group.label}>
							<span className='nav-group-label'>
								{group.label}
							</span>
							{group.items.map(
								({
									label,
									slug,
									icon: Icon,
								}) => {
									const href = `/projects/${activeProject.id}/${slug === 'knowledge' ? 'source/documents' : slug}`;
									const isActive =
										slug ===
										'knowledge'
											? pathname.startsWith(
													`/projects/${activeProject.id}/source`,
												)
											: pathname.startsWith(
													href,
												);
									return (
										<SmoothLink
											href={
												href
											}
											key={
												slug
											}
											className={
												isActive
													? 'active'
													: ''
											}>
											<Icon
												size={
													16
												}
											/>
											<span>
												{
													label
												}
											</span>
										</SmoothLink>
									);
								},
							)}
						</div>
					))}
					<div className='nav-group nav-settings'>
						<SmoothLink
							href={`/projects/${activeProject.id}/settings`}
							className={
								pathname.startsWith(
									`/projects/${activeProject.id}/settings`,
								)
									? 'active'
									: ''
							}>
							<Settings size={16} />
							<span>
								Project settings
							</span>
						</SmoothLink>
					</div>
				</div>
			)}
			{!activeProject && (
				<div className='nav-guidance'>
					<Layers3 size={18} />
					<strong>Select a project</strong>
					<p>Project tools will appear here.</p>
				</div>
			)}
		</nav>
	);
}
