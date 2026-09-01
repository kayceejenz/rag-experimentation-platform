import {
	Bot,
	Database,
	FlaskConical,
	Gauge,
	Layers3,
	PlayCircle,
} from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type { Project } from '@/types/workspace';

export function ProjectOverview({ project }: { project: Project }) {
	const assets = [
		{
			title: 'Knowledge Base',
			description:
				'Manage project documents, ingestion pipelines, traces, and lineage.',
			icon: Database,
			href: `/projects/${project.id}/source/documents`,
		},
		{
			title: 'Indexes',
			description:
				'Immutable embedding, chunking, and vector index versions derived from project knowledge.',
			icon: Layers3,
			href: `/projects/${project.id}/indexes`,
		},
		{
			title: 'Experiments',
			description:
				'Compare retrieval and generation configurations without overwriting history.',
			icon: FlaskConical,
			href: `/projects/${project.id}/experiments`,
		},
		{
			title: 'Benchmarks',
			description:
				'Golden datasets and repeatable evaluation suites shared by the project.',
			icon: Gauge,
			href: `/projects/${project.id}/benchmarks`,
		},
		{
			title: 'Assistants',
			description:
				'Deployable action units bound to immutable project configurations.',
			icon: Bot,
			href: `/projects/${project.id}/assistants`,
		},
		{
			title: 'Runs',
			description:
				'Monitor executions, inspect traces, and review lineage across the project.',
			icon: PlayCircle,
			href: `/projects/${project.id}/runs`,
		},
	];
	return (
		<div className='project-overview'>
			<header className='project-overview-header'>
				<div>
					<span className='eyebrow'>Project</span>
					<h1>{project.name}</h1>
					{project.description && (
						<p className='project-description'>
							{project.description}
						</p>
					)}
				</div>
			</header>
			<div className='foundation-grid project-foundation-grid'>
				{assets.map(
					({
						title,
						description,
						icon: Icon,
						href,
					}) => (
						<SmoothLink
							key={title}
							href={href}
							className='foundation-card'>
							<span>
								<Icon
									size={
										19
									}
								/>
							</span>
							<div>
								<h2>{title}</h2>
								<p>
									{
										description
									}
								</p>
							</div>
						</SmoothLink>
					),
				)}
			</div>
		</div>
	);
}
