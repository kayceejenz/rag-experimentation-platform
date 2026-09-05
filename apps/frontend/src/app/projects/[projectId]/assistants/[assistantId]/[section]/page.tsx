import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { SmoothLink } from '@/components/navigation/smooth-link';
import { ProjectAccessDenied } from '@/components/projects/project-access-denied';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Assistant, Project } from '@/types/workspace';
import { AssistantLineage, type AssistantLineageData } from '@/components/assistants/assistant-lineage';
import { AssistantPlayground } from '@/components/assistants/assistant-playground';

const sections: Record<string, { title: string; description: string }> = {
	playground: {
		title: 'Playground',
		description:
			'An interactive surface for testing the active assistant revision.',
	},
	lineage: {
		title: 'Lineage',
		description:
			'The immutable path from a completed experiment run to the active assistant revision.',
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
	const project = projects.find(item => item.id === projectId);
	if (project && project.role !== 'owner' && !project.permissions?.assistants?.view) {
		return <AppShell user={{ id: user.id, email: user.email, name: user.name }} projects={projects} activeProjectId={projectId}><ProjectAccessDenied projectId={projectId} feature='Assistants'/></AppShell>;
	}
	if (!assistant || assistant.project_id !== projectId) notFound();
	const lineage = section === 'lineage' ? await backendJson<AssistantLineageData>(user.accessToken, `/assistants/${assistantId}/lineage`).catch(() => null) : null;
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
			{section === 'playground' ? (
				<AssistantPlayground assistant={assistant} />
			) : lineage ? (
				<AssistantLineage lineage={lineage} />
			) : (
				<section className='foundation-placeholder'>
					<h2>No lineage available</h2>
					<p>This assistant was not created from a completed experiment run.</p>
				</section>
			)}
		</AppShell>
	);
}
