import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { AssistantOverview } from '@/components/assistants/assistant-overview';
import { ProjectAccessDenied } from '@/components/projects/project-access-denied';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Assistant, Project } from '@/types/workspace';

type Props = { params: Promise<{ projectId: string; assistantId: string }> };

export default async function AssistantPage({ params }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId, assistantId } = await params;
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
	if (!assistant || !project || assistant.project_id !== projectId)
		notFound();
	return (
		<AppShell
			user={{
				id: user.id,
				email: user.email,
				name: user.name,
			}}
			projects={projects}
			activeProjectId={projectId}>
			<AssistantOverview
				project={project}
				assistant={assistant}
			/>
		</AppShell>
	);
}
