import { notFound } from 'next/navigation';
import { Activity, Construction } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { SmoothLink } from '@/components/navigation/smooth-link';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Assistant, Project } from '@/types/workspace';

const sections: Record<string, { title: string; description: string }> = {
	playground: {
		title: 'Playground',
		description:
			'An interactive surface for testing the active assistant revision.',
	},
	conversations: {
		title: 'Conversations',
		description: 'Independent sessions and their message history.',
	},
	runs: {
		title: 'Runs',
		description:
			'Execution history with trace, lineage, evaluation, and logs.',
	},
	deployments: {
		title: 'Deployments',
		description:
			'Environment-specific releases of immutable assistant revisions.',
	},
};

type Props = {
	params: Promise<{
		projectId: string;
		assistantId: string;
		section: string;
	}>;
};
export default async function AssistantSection({ params }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId, assistantId, section } = await params;
	const definition = sections[section];
	if (!definition) notFound();
	const [assistant, projects] = await Promise.all([
		backendJson<Assistant>(
			user.accessToken,
			`/assistants/${assistantId}`,
		).catch(() => null),
		backendJson<{ projects: Project[] }>(
			user.accessToken,
			'/projects',
		)
			.then(value => value.projects)
			.catch(() => []),
	]);
	if (!assistant || assistant.project_id !== projectId) notFound();
	const base = `/projects/${projectId}/assistants/${assistantId}`;
	return (
		<AppShell
			user={{
				id: user.id,
				email: user.email,
				name: user.name,
			}}
			projects={projects}
			activeProjectId={projectId}
			title={definition.title}
			description={definition.description}
			tabs={
				<>
					<SmoothLink href={base}>
						Overview
					</SmoothLink>
					{Object.keys(sections).map(key => (
						<SmoothLink
							key={key}
							href={`${base}/${key}`}
							className={
								key === section
									? 'active'
									: ''
							}>
							{sections[key].title}
						</SmoothLink>
					))}
				</>
			}>
			<section className='foundation-placeholder'>
				<span>
					<Construction size={22} />
				</span>
				<h2>{definition.title} structure</h2>
				<p>
					This boundary is intentionally
					non-functional. Its workflows and data
					contracts will be implemented
					independently.
				</p>
				{section === 'runs' && (
					<div className='run-detail-preview'>
						<Activity size={17} />
						<span>
							Run detail: Summary ·
							Trace · Lineage ·
							Evaluation · Logs
						</span>
					</div>
				)}
			</section>
		</AppShell>
	);
}
