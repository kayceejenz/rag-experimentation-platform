import { notFound } from 'next/navigation';
import { SourceOverview } from '@/components/sources/source-overview';
import { ProjectAccessDenied } from '@/components/projects/project-access-denied';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type {
	KnowledgeActivityEvent,
	KnowledgeBase,
	KnowledgeFolder,
	Project,
	Source,
} from '@/types/workspace';

const sections = new Set(['documents', 'activity']);
type Props = { params: Promise<{ projectId: string; section: string }> };
export default async function SourceSectionPage({ params }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId, section } = await params;
	if (!sections.has(section)) notFound();
	const [project, source] = await Promise.all([
		backendJson<Project>(user.accessToken, `/projects/${projectId}`).catch(() => null),
		backendJson<KnowledgeBase>(user.accessToken, `/projects/${projectId}/source`).catch(() => null),
	]);
	if (!project) notFound();
	if (project.role !== 'owner' && !project.permissions?.knowledge?.view) {
		return <ProjectAccessDenied projectId={projectId} feature='Knowledge Base'/>;
	}
	if (!source) notFound();
	const [documents, activity, folders] = await Promise.all([
		backendJson<{ sources: Source[] }>(
			user.accessToken,
			`/knowledge-bases/${source.id}/sources`,
		)
			.then(value => value.sources)
			.catch(() => []),
		backendJson<{ events: KnowledgeActivityEvent[] }>(
			user.accessToken,
			`/knowledge-bases/${source.id}/activity`,
		)
			.then(value => value.events)
			.catch(() => []),
		backendJson<{ folders: KnowledgeFolder[] }>(
			user.accessToken,
			`/knowledge-bases/${source.id}/folders`,
		)
			.then(value => value.folders)
			.catch(() => []),
	]);
	return <SourceOverview
				project={project}
				source={source}
				initialDocuments={documents}
				initialActivity={activity}
				initialFolders={folders}
				active={section}
			/>;
}
