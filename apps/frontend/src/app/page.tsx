import { AppShell } from '@/components/layout/app-shell';
import { WorkspaceOverview, type WorkspaceOverviewData } from '@/components/workspace/workspace-overview';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Execution } from '@/types/trace';
import type { Assistant, Project } from '@/types/workspace';

type IndexBuild = { id: string; job_count: number; completed_jobs: number; failed_jobs: number; active_jobs: number };

async function overviewData(accessToken: string, projects: Project[]): Promise<WorkspaceOverviewData> {
	const snapshots = await Promise.all(projects.map(async project => {
		const [indexes, assistants, executions] = await Promise.all([
			backendJson<{ indexes: IndexBuild[] }>(accessToken, `/projects/${project.id}/indexes`).catch(() => ({ indexes: [] })),
			backendJson<{ assistants: Assistant[] }>(accessToken, `/projects/${project.id}/assistants`).catch(() => ({ assistants: [] })),
			backendJson<{ executions: Execution[] }>(accessToken, `/projects/${project.id}/executions?limit=100`).catch(() => ({ executions: [] })),
		]);
		return { project, indexes: indexes.indexes, assistants: assistants.assistants, executions: executions.executions };
	}));
	const allIndexes = snapshots.flatMap(snapshot => snapshot.indexes);
	const allExecutions = snapshots.flatMap(snapshot => snapshot.executions);
	return {
		indexCount: allIndexes.length,
		readyIndexes: allIndexes.filter(index => index.job_count > 0 && index.completed_jobs === index.job_count).length,
		buildingIndexes: allIndexes.filter(index => index.active_jobs > 0).length,
		activeAssistants: snapshots.flatMap(snapshot => snapshot.assistants).filter(assistant => assistant.status === 'active').length,
		failedRuns: allExecutions.filter(execution => execution.status === 'failed').length,
		projectStatuses: snapshots.map(snapshot => ({
			projectId: snapshot.project.id,
			indexCount: snapshot.indexes.length,
			activeRuns: snapshot.executions.filter(execution => execution.status === 'running' || execution.status === 'pending').length,
			failedRuns: snapshot.executions.filter(execution => execution.status === 'failed').length,
			lastActivity: snapshot.executions[0]?.created_at ?? null,
		})),
		recentExecutions: snapshots.flatMap(snapshot => snapshot.executions.map(execution => ({ ...execution, projectName: snapshot.project.name }))).sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()).slice(0, 8),
	};
}

export default async function Home() {
	const user = await getAuthUser();
	const projects = user
		? await backendJson<{ projects: Project[] }>(user.accessToken, '/projects')
				.then(result => result.projects)
				.catch(() => [])
		: [];
	const data: WorkspaceOverviewData = user
		? await overviewData(user.accessToken, projects)
		: { indexCount: 0, readyIndexes: 0, buildingIndexes: 0, activeAssistants: 0, failedRuns: 0, projectStatuses: [], recentExecutions: [] };
	return (
		<AppShell
			user={user ? { id: user.id, email: user.email, name: user.name } : undefined}
			projects={projects}
			activeNavigation='bots'>
			<WorkspaceOverview projects={projects} data={data} />
		</AppShell>
	);
}
