'use client';

import { usePathname } from 'next/navigation';
import {
	Bot,
	ChevronDown,
	Database,
	FlaskConical,
	FolderKanban,
	Gauge,
	Home,
	Layers3,
	FileCode2,
	Settings,
} from 'lucide-react';
import { SmoothLink, useSmoothNavigation } from '@/components/navigation/smooth-link';
import type { Project, ProjectFeature } from '@/types/workspace';

const projectItems = [
	{
		label: 'Knowledge Base',
		slug: 'knowledge',
		icon: Database,
	},
	{
		label: 'Indexes',
		slug: 'indexes',
		icon: Layers3,
	},
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
	{ label: 'Prompts', slug: 'prompts', icon: FileCode2 },
	{ label: 'Assistants', slug: 'assistants', icon: Bot },
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
	const navigate = useSmoothNavigation();
	const resolvedProjectId =
		activeProjectId ??
		projects.find(project => project.is_default)?.id ??
		projects[0]?.id;
	const activeProject = projects.find(
		project => project.id === resolvedProjectId,
	);
	const canView = (feature: ProjectFeature) =>
		activeProject?.role === 'owner' ||
		Boolean(activeProject?.permissions?.[feature]?.view);
	return (
		<nav
			className={
				compact
					? 'structured-nav compact'
					: 'structured-nav'
			}
			aria-label='Workspace navigation'>
			<div className='nav-group'>
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
								navigate(`/projects/${event.target.value}`)
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
					<div className='nav-group'>
						{projectItems
							.filter(item =>
								canView(
									item.slug as ProjectFeature,
								),
							)
							.map(
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
											href={href}
											key={slug}
											className={
												isActive
													? 'active'
													: ''
											}>
											<Icon size={16} />
											<span>{label}</span>
										</SmoothLink>
									);
								},
							)}
					</div>
					{canView('settings') && (
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
								<Settings
									size={
										16
									}
								/>
								<span>
									Project
									settings
								</span>
							</SmoothLink>
						</div>
					)}
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
