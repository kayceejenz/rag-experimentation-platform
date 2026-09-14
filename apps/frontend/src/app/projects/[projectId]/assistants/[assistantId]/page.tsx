import { notFound } from 'next/navigation';
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
	const [assistant, project] = await Promise.all([
		backendJson<Assistant>(
			user.accessToken,
			`/assistants/${assistantId}`,
		).catch(() => null),
		backendJson<Project>(
			user.accessToken,
			`/projects/${projectId}`,
		).catch(() => null),
	]);
	if (
		project &&
		project.role !== 'owner' &&
		!project.permissions?.assistants?.view
	) {
		return (
			<ProjectAccessDenied
				projectId={projectId}
				feature='Assistants'
			/>
		);
	}
	if (!assistant || !project || assistant.project_id !== projectId)
		notFound();
	return <AssistantOverview project={project} assistant={assistant} />;
}
