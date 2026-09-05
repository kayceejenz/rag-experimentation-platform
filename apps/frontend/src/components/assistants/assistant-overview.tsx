import { Boxes, GitBranch, TestTube2 } from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type { Assistant, Project } from '@/types/workspace';

export function AssistantOverview({
	project,
	assistant,
}: {
	project: Project;
	assistant: Assistant;
}) {
	const base = `/projects/${project.id}/assistants/${assistant.id}`;
	const sections = [
		{
			title: 'Playground',
			description:
				'Try prompts against the active assistant revision.',
			icon: TestTube2,
			href: `${base}/playground`,
		},
		{
			title: 'Lineage',
			description:
				'Trace the tested experiment configuration promoted into this assistant.',
			icon: GitBranch,
			href: `${base}/lineage`,
		},
	];
	return (
		<div className='assistant-foundation'>
			<header className='bot-console-hero'>
				<div className='bot-console-identity'>
					<div>
						<h1>{assistant.name}</h1>
						<p>
							{assistant.description ||
								'A deployable action unit bound to a versioned project configuration.'}
						</p>
					</div>
				</div>
				<span
					className={`bot-status ${assistant.status}`}>
					{assistant.status}
				</span>
			</header>
			<nav
				className='bot-console-tabs'
				aria-label='Assistant sections'>
				<SmoothLink href={base} className='active'>
					Overview
				</SmoothLink>
				{sections.map(item => (
					<SmoothLink
						key={item.title}
						href={item.href}>
						{item.title}
					</SmoothLink>
				))}
			</nav>
			<div className='foundation-grid'>
				{sections.map(
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
							<Boxes size={15} />
						</SmoothLink>
					),
				)}
			</div>
		</div>
	);
}
