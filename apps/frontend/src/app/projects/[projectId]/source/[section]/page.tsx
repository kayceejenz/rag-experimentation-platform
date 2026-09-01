import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { SourceOverview } from '@/components/sources/source-overview';
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
	const projects = await backendJson<{ projects: Project[] }>(
		user.accessToken,
		'/projects',
	)
		.then(value => value.projects)
		.catch(() => []);
	const project = projects.find(item => item.id === projectId);
	if (!project) notFound();
	const source = await backendJson<KnowledgeBase>(
		user.accessToken,
		`/projects/${projectId}/source`,
	).catch(() => null);
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
	return (
		<AppShell
			user={{
				id: user.id,
				email: user.email,
				name: user.name,
			}}
			projects={projects}
			activeProjectId={projectId}>
			<SourceOverview
				project={project}
				source={source}
				initialDocuments={documents}
				initialActivity={activity}
				initialFolders={folders}
				active={section}
			/>
		</AppShell>
	);
}
