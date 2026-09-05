import {
	Activity,
	Bot,
	CircleCheck,
	Clock3,
	FolderKanban,
	Layers3,
	TriangleAlert,
} from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import type { Execution, ExecutionStatus } from '@/types/trace';
import type { Project } from '@/types/workspace';

export type WorkspaceProjectStatus = {
	projectId: string;
	indexCount: number;
	activeRuns: number;
	failedRuns: number;
	lastActivity: string | null;
};
export type WorkspaceOverviewData = {
	indexCount: number;
	readyIndexes: number;
	buildingIndexes: number;
	activeAssistants: number;
	failedRuns: number;
	projectStatuses: WorkspaceProjectStatus[];
	recentExecutions: Array<Execution & { projectName: string }>;
};

function relativeTime(value: string) {
	const minutes = Math.floor(
		Math.max(0, Date.now() - new Date(value).getTime()) / 60_000,
	);
	if (minutes < 1) return 'just now';
	if (minutes < 60) return `${minutes}m ago`;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.floor(hours / 24);
	return days === 1 ? 'yesterday' : `${days}d ago`;
}

function executionLabel(kind: string) {
	return kind
		.replaceAll('_', ' ')
		.replace(/\b\w/g, character => character.toUpperCase());
}

function StatusIcon({ status }: { status: ExecutionStatus }) {
	if (status === 'completed') return <CircleCheck size={15} />;
	if (status === 'failed') return <TriangleAlert size={15} />;
	if (status === 'running') return <Activity size={15} />;
	return <Clock3 size={15} />;
}

export function WorkspaceOverview({
	projects,
	data,
}: {
	projects: Project[];
	data: WorkspaceOverviewData;
}) {
	const statuses = new Map(
		data.projectStatuses.map(status => [status.projectId, status]),
	);
	return (
		<div className='product-overview'>
			<header className='product-page-header'>
				<div>
					<h1>Overview</h1>
					<p>
						Current workspace health and
						recent pipeline activity.
					</p>
				</div>
			</header>
			<div className='overview-metrics'>
				<div>
					<FolderKanban size={18} />
					<span>
						<strong>
							{projects.length}
						</strong>
						<small>Projects</small>
					</span>
				</div>
				<div>
					<Layers3 size={18} />
					<span>
						<strong>
							{data.indexCount}
						</strong>
						<small>
							Indexes ·{' '}
							{data.readyIndexes}{' '}
							ready
						</small>
					</span>
				</div>
				<div>
					<Bot size={18} />
					<span>
						<strong>
							{data.activeAssistants}
						</strong>
						<small>Active assistants</small>
					</span>
				</div>
				<div>
					<TriangleAlert size={18} />
					<span>
						<strong>
							{data.failedRuns}
						</strong>
						<small>Failed runs</small>
					</span>
				</div>
			</div>
			<div className='overview-layout'>
				<section className='overview-panel'>
					<header>
						<div>
							<h2>Projects</h2>
							<p>
								Live status
								across the
								workspace.
							</p>
						</div>
						<SmoothLink href='/projects'>
							View all
						</SmoothLink>
					</header>
					<div className='workspace-project-list overview-project-status-list'>
						{projects
							.slice(0, 5)
							.map(project => {
								const status =
									statuses.get(
										project.id,
									);
								return (
									<SmoothLink
										href={`/projects/${project.id}`}
										key={
											project.id
										}>
										<span>
											{project.name
												.slice(
													0,
													1,
												)
												.toUpperCase()}
										</span>
										<div>
											<strong>
												{
													project.name
												}
											</strong>
											<small>
												{status?.indexCount ??
													0}{' '}
												indexes
												·{' '}
												{status?.activeRuns ??
													0}{' '}
												active
												runs
											</small>
										</div>
										<time>
											{status?.lastActivity
												? relativeTime(
														status.lastActivity,
													)
												: 'No activity'}
										</time>
									</SmoothLink>
								);
							})}
						{projects.length === 0 && (
							<div className='mock-empty'>
								No projects yet.
							</div>
						)}
					</div>
				</section>
				<section className='overview-panel'>
					<header>
						<div>
							<h2>Recent activity</h2>
							<p>
								Latest execution
								events across
								all projects.
							</p>
						</div>
					</header>
					<div className='overview-activity-list'>
						{data.recentExecutions.map(
							execution => (
								<SmoothLink
									href={`/projects/${execution.project_id}/runs`}
									key={
										execution.id
									}>
									<span
										className={`overview-run-icon ${execution.status}`}>
										<StatusIcon
											status={
												execution.status
											}
										/>
									</span>
									<p>
										<strong>
											{executionLabel(
												execution.kind,
											)}
										</strong>
										<small>
											{
												execution.projectName
											}{' '}
											·{' '}
											{relativeTime(
												execution.created_at,
											)}
										</small>
									</p>
									<em
										className={`catalog-state ${execution.status}`}>
										{
											execution.status
										}
									</em>
								</SmoothLink>
							),
						)}
						{!data.recentExecutions
							.length && (
							<div className='mock-empty'>
								No pipeline
								activity yet.
							</div>
						)}
					</div>
				</section>
			</div>
			{data.buildingIndexes > 0 && (
				<div className='overview-live-note'>
					<Activity size={14} />
					<span>
						{data.buildingIndexes} index{' '}
						{data.buildingIndexes === 1
							? 'build is'
							: 'builds are'}{' '}
						currently in progress.
					</span>
				</div>
			)}
		</div>
	);
}
