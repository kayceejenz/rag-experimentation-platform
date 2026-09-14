import { AppShell } from '@/components/layout/app-shell';
import {
	WorkspaceOverview,
	type WorkspaceOverviewData,
} from '@/components/workspace/workspace-overview';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Project } from '@/types/workspace';

type OverviewResponse = {
	projects: Project[];
	index_count: number;
	ready_indexes: number;
	building_indexes: number;
	active_assistants: number;
	failed_runs: number;
	project_statuses: Array<{
		project_id: string;
		index_count: number;
		active_runs: number;
		failed_runs: number;
		last_activity: string | null;
	}>;
	recent_executions: Array<
		WorkspaceOverviewData['recentExecutions'][number] & {
			project_name: string;
		}
	>;
};

const EMPTY_OVERVIEW: WorkspaceOverviewData = {
	indexCount: 0,
	readyIndexes: 0,
	buildingIndexes: 0,
	activeAssistants: 0,
	failedRuns: 0,
	projectStatuses: [],
	recentExecutions: [],
};

export default async function Home() {
	const user = await getAuthUser();
	const overview = user
		? await backendJson<OverviewResponse>(
				user.accessToken,
				'/projects/overview',
			).catch(() => null)
		: null;
	const projects = overview?.projects ?? [];
	const data: WorkspaceOverviewData = overview
		? {
				indexCount: overview.index_count,
				readyIndexes: overview.ready_indexes,
				buildingIndexes: overview.building_indexes,
				activeAssistants: overview.active_assistants,
				failedRuns: overview.failed_runs,
				projectStatuses: overview.project_statuses.map(
					status => ({
						projectId: status.project_id,
						indexCount: status.index_count,
						activeRuns: status.active_runs,
						failedRuns: status.failed_runs,
						lastActivity:
							status.last_activity,
					}),
				),
				recentExecutions:
					overview.recent_executions.map(
						execution => ({
							...execution,
							projectName:
								execution.project_name,
						}),
					),
			}
		: EMPTY_OVERVIEW;
	return (
		<AppShell
			user={
				user
					? {
							id: user.id,
							email: user.email,
							name: user.name,
						}
					: undefined
			}
			projects={projects}
			activeNavigation='bots'>
			<WorkspaceOverview projects={projects} data={data} />
		</AppShell>
	);
}
