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
import type { ExperimentRun } from '@/types/trace';

export function ProjectOverview({ project, experimentRuns = [] }: { project: Project; experimentRuns?: ExperimentRun[] }) {
	const experiments = new Set(experimentRuns.map(run => run.experiment_id)).size;
	const variants = new Set(experimentRuns.map(run => run.variant_id)).size;
	const assistants = new Set(experimentRuns.flatMap(run => run.assistant_id ? [run.assistant_id] : [])).size;
	const latest = experimentRuns[0];
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
			<section className='project-lineage-summary' aria-label='Experiment lineage summary'>
				<div><strong>{experiments}</strong><span>Experiments run</span></div>
				<div><strong>{variants}</strong><span>Variants evaluated</span></div>
				<div><strong>{assistants}</strong><span>Assistants promoted</span></div>
				<div className='project-lineage-latest'>
					<strong>{latest ? latest.variant_name : 'No runs yet'}</strong>
					<span>{latest ? `${latest.experiment_name} · ${latest.assistant_name ?? 'Not promoted'}` : 'Run a variant to establish lineage'}</span>
				</div>
			</section>
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
