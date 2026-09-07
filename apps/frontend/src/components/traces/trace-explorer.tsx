'use client';

import {
	Activity,
	Box,
	Check,
	ChevronRight,
	CircleAlert,
	Clock3,
	Copy,
	Database,
	FileInput,
	GitBranch,
	LoaderCircle,
	RefreshCw,
	Search,
	ServerCog,
	Workflow,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { SmoothLink } from '@/components/navigation/smooth-link';
import { formatDateTimeWithSeconds } from '@/lib/format';
import type { Project } from '@/types/workspace';
import type {
	ArtifactLink,
	Execution,
	ExecutionLineage,
	ExecutionStatus,
	ExperimentRun,
} from '@/types/trace';

type Tab = 'lineage' | 'trace';

type Props = {
	project: Project;
	initialExecutions: Execution[];
	initialLineage: ExecutionLineage | null;
	initialExperimentRuns: ExperimentRun[];
	resources?: {
		sources: Array<{
			id: string;
			display_name: string;
			version: number;
		}>;
		indexes: Array<{ id: string; name: string }>;
	};
};

const statusLabels: Record<ExecutionStatus, string> = {
	pending: 'Pending',
	running: 'Running',
	completed: 'Succeeded',
	failed: 'Failed',
	cancelled: 'Cancelled',
};

function formatDate(value: string | null): string {
	if (!value) return '—';
	return formatDateTimeWithSeconds(value);
}

function duration(execution: Execution): string {
	if (!execution.started_at) return 'Not started';
	if (!execution.completed_at) return 'In progress';
	const end = new Date(execution.completed_at).getTime();
	const milliseconds = Math.max(
		0,
		end - new Date(execution.started_at).getTime(),
	);
	if (milliseconds < 1000) return `${milliseconds} ms`;
	if (milliseconds < 60_000)
		return `${(milliseconds / 1000).toFixed(1)} s`;
	const minutes = Math.floor(milliseconds / 60_000);
	const seconds = Math.round((milliseconds % 60_000) / 1000);
	return `${minutes}m ${seconds}s`;
}

function shortId(value: string): string {
	return value.slice(0, 8);
}

function artifactLabel(link: ArtifactLink): string {
	return link.artifact.kind.replaceAll('_', ' ');
}

export function TraceExplorer({
	project,
	initialExecutions,
	initialLineage,
	initialExperimentRuns,
	resources = { sources: [], indexes: [] },
}: Props) {
	const [executions, setExecutions] = useState(initialExecutions);
	const [experimentRuns, setExperimentRuns] = useState(
		initialExperimentRuns,
	);
	const [selectedId, setSelectedId] = useState(
		initialLineage?.execution.id ?? null,
	);
	const [lineage, setLineage] = useState(initialLineage);
	const [tab, setTab] = useState<Tab>('lineage');
	const [query, setQuery] = useState('');
	const [status, setStatus] = useState<'all' | ExecutionStatus>('all');
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const filtered = useMemo(() => {
		const needle = query.trim().toLowerCase();
		return executions.filter(execution => {
			if (status !== 'all' && execution.status !== status)
				return false;
			return (
				!needle ||
				execution.id.toLowerCase().includes(needle) ||
				execution.kind.toLowerCase().includes(needle) ||
				execution.code_revision
					.toLowerCase()
					.includes(needle)
			);
		});
	}, [executions, query, status]);

	const selected = lineage?.execution.id === selectedId ? lineage : null;
	const successful = executions.filter(
		item => item.status === 'completed',
	).length;
	const failed = executions.filter(
		item => item.status === 'failed',
	).length;
	const active = executions.filter(item =>
		['pending', 'running'].includes(item.status),
	).length;
	function resource(execution: Execution) {
		const index = resources.indexes.find(
			item => item.id === execution.specification_id,
		);
		if (index)
			return {
				label: index.name,
				href: `/projects/${project.id}/indexes`,
			};
		const source = resources.sources.find(
			item => item.id === execution.parameters.source_id,
		);
		if (source)
			return {
				label: `${source.display_name} · v${source.version}`,
				href: `/projects/${project.id}/source/documents`,
			};
		return {
			label: execution.knowledge_base_id
				? 'Knowledge Base'
				: 'Project',
			href: execution.knowledge_base_id
				? `/projects/${project.id}/source/documents`
				: `/projects/${project.id}`,
		};
	}

	async function selectExecution(executionId: string) {
		setSelectedId(executionId);
		setTab('lineage');
		setLoading(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/executions/${executionId}`,
			);
			if (!response.ok)
				throw new Error(
					'Could not load this execution.',
				);
			setLineage((await response.json()) as ExecutionLineage);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Could not load this execution.',
			);
		} finally {
			setLoading(false);
		}
	}

	async function refresh() {
		setLoading(true);
		setError(null);
		try {
			const response = await fetch(
				`/api/projects/${project.id}/executions?limit=100`,
			);
			if (!response.ok)
				throw new Error(
					'Could not refresh executions.',
				);
			const body = (await response.json()) as {
				executions: Execution[];
			};
			setExecutions(body.executions);
			const experimentResponse = await fetch(
				`/api/projects/${project.id}/experiment-runs`,
			);
			if (experimentResponse.ok) {
				const experimentBody =
					(await experimentResponse.json()) as {
						runs: ExperimentRun[];
					};
				setExperimentRuns(experimentBody.runs);
			}
			if (selectedId) await selectExecution(selectedId);
		} catch (caught) {
			setError(
				caught instanceof Error
					? caught.message
					: 'Refresh failed.',
			);
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className='trace-workspace'>
			<section className='trace-hero'>
				<div>
					<span className='trace-eyebrow'>
						Observability / {project.name}
					</span>
					<h1>Runs</h1>
					<p>
						Project-wide execution history
						for Knowledge and Index
						operations.
					</p>
				</div>
				<button
					className='trace-refresh'
					onClick={refresh}
					disabled={loading}>
					<RefreshCw
						size={15}
						className={
							loading ? 'spin' : ''
						}
					/>
					Refresh
				</button>
			</section>

			<section
				className='trace-metrics'
				aria-label='Execution summary'>
				<div>
					<Activity size={17} />
					<span>
						<strong>
							{executions.length}
						</strong>
						<small>Total runs</small>
					</span>
				</div>
				<div>
					<Check size={17} />
					<span>
						<strong>{successful}</strong>
						<small>Succeeded</small>
					</span>
				</div>
				<div>
					<CircleAlert size={17} />
					<span>
						<strong>{failed}</strong>
						<small>Failed</small>
					</span>
				</div>
				<div>
					<LoaderCircle size={17} />
					<span>
						<strong>{active}</strong>
						<small>In progress</small>
					</span>
				</div>
			</section>

			{error && (
				<div className='trace-error' role='alert'>
					{error}
				</div>
			)}

			<section className='trace-runs-panel experiment-run-panel'>
				<div className='trace-panel-heading'>
					<div>
						<h2>Experiment runs</h2>
						<p>
							Evaluated variants and
							their promoted
							assistants
						</p>
					</div>
				</div>
				<div className='trace-table-wrap'>
					<table className='trace-table'>
						<thead>
							<tr>
								<th>Run</th>
								<th>
									Experiment
								</th>
								<th>Variant</th>
								<th>
									Assistant
								</th>
								<th>State</th>
								<th>Started</th>
							</tr>
						</thead>
						<tbody>
							{experimentRuns.map(
								run => (
									<tr
										key={
											run.variant_run_id
										}>
										<td>
											<strong>
												{shortId(
													run.run_id,
												)}
											</strong>
											<small className='trace-cell-note'>
												Revision{' '}
												{
													run.code_revision
												}
											</small>
										</td>
										<td>
											<SmoothLink
												href={`/projects/${project.id}/experiments`}>
												{
													run.experiment_name
												}
											</SmoothLink>
										</td>
										<td>
											{
												run.variant_name
											}
										</td>
										<td>
											{run.assistant_id ? (
												<SmoothLink
													href={`/projects/${project.id}/assistants/${run.assistant_id}`}>
													{
														run.assistant_name
													}
													<small className='trace-cell-note'>
														Revision
														v
														{
															run.assistant_revision
														}
													</small>
												</SmoothLink>
											) : (
												<span className='trace-muted'>
													Not
													promoted
												</span>
											)}
										</td>
										<td>
											<span
												className={`trace-status ${run.variant_status}`}>
												{
													statusLabels[
														run
															.variant_status
													]
												}
											</span>
										</td>
										<td>
											{formatDate(
												run.started_at ??
													run.created_at,
											)}
										</td>
									</tr>
								),
							)}
						</tbody>
					</table>
					{experimentRuns.length === 0 && (
						<div className='trace-empty'>
							<Workflow size={28} />
							<strong>
								No experiment
								runs
							</strong>
							<span>
								Run an
								experiment
								variant to
								establish
								evaluation
								lineage.
							</span>
						</div>
					)}
				</div>
			</section>

			<section className='trace-runs-panel'>
				<div className='trace-panel-heading'>
					<div>
						<h2>Run history</h2>
						<p>
							Most recent 100
							executions
						</p>
					</div>
					<div className='trace-filters'>
						<label>
							<Search size={14} />
							<input
								value={query}
								onChange={event =>
									setQuery(
										event
											.target
											.value,
									)
								}
								placeholder='Search run ID, type, revision'
							/>
						</label>
						<select
							value={status}
							onChange={event =>
								setStatus(
									event
										.target
										.value as typeof status,
								)
							}
							aria-label='Filter by status'>
							<option value='all'>
								All states
							</option>
							<option value='completed'>
								Succeeded
							</option>
							<option value='running'>
								Running
							</option>
							<option value='pending'>
								Pending
							</option>
							<option value='failed'>
								Failed
							</option>
							<option value='cancelled'>
								Cancelled
							</option>
						</select>
					</div>
				</div>
				<div className='trace-table-wrap'>
					<table className='trace-table'>
						<thead>
							<tr>
								<th>Run</th>
								<th>State</th>
								<th>
									Operation
								</th>
								<th>
									Resource
								</th>
								<th>Started</th>
								<th>
									Duration
								</th>
								<th>
									<span className='sr-only'>
										Open
									</span>
								</th>
							</tr>
						</thead>
						<tbody>
							{filtered.map(
								execution => (
									<tr
										key={
											execution.id
										}
										className={
											selectedId ===
											execution.id
												? 'selected'
												: ''
										}
										onClick={() =>
											selectExecution(
												execution.id,
											)
										}>
										<td>
											<button className='trace-run-link'>
												<span className='trace-run-icon'>
													<Workflow
														size={
															15
														}
													/>
												</span>
												<span>
													<strong>
														{execution.kind.replaceAll(
															'_',
															' ',
														)}
													</strong>
													<small>
														{shortId(
															execution.id,
														)}
													</small>
												</span>
											</button>
										</td>
										<td>
											<span
												className={`trace-status ${execution.status}`}>
												{execution.status !==
													'completed' && (
													<i />
												)}
												{
													statusLabels[
														execution
															.status
													]
												}
											</span>
										</td>
										<td>
											{execution.kind.replaceAll(
												'_',
												' ',
											)}
										</td>
										<td>
											{
												resource(
													execution,
												)
													.label
											}
										</td>
										<td>
											{formatDate(
												execution.started_at ??
													execution.created_at,
											)}
										</td>
										<td>
											{duration(
												execution,
											)}
										</td>
										<td>
											<ChevronRight
												size={
													15
												}
											/>
										</td>
									</tr>
								),
							)}
						</tbody>
					</table>
					{filtered.length === 0 && (
						<div className='trace-empty'>
							<Workflow size={28} />
							<strong>
								No matching
								executions
							</strong>
							<span>
								Run an ingestion
								job or adjust
								the filters.
							</span>
						</div>
					)}
				</div>
			</section>

			<section className='trace-detail-panel'>
				{loading && !selected ? (
					<div className='trace-detail-loading'>
						<LoaderCircle
							className='spin'
							size={22}
						/>{' '}
						Loading execution…
					</div>
				) : selected ? (
					<>
						<div className='trace-detail-header'>
							<div>
								<span
									className={`trace-status ${selected.execution.status}`}>
									{selected
										.execution
										.status !==
										'completed' && (
										<i />
									)}
									{
										statusLabels[
											selected
												.execution
												.status
										]
									}
								</span>
								<h2>
									{selected.execution.kind.replaceAll(
										'_',
										' ',
									)}{' '}
									execution
								</h2>
								<button
									onClick={() =>
										navigator.clipboard.writeText(
											selected
												.execution
												.id,
										)
									}
									title='Copy execution ID'>
									{
										selected
											.execution
											.id
									}
									<Copy
										size={
											13
										}
									/>
								</button>
							</div>
							<div className='trace-detail-facts'>
								<span>
									<Clock3
										size={
											14
										}
									/>
									{duration(
										selected.execution,
									)}
								</span>
								<span>
									<ServerCog
										size={
											14
										}
									/>
									{selected
										.execution
										.worker_id ??
										'Unassigned'}
								</span>
								<span>
									Attempt
									#
									{
										selected
											.execution
											.attempt
									}
								</span>
								<SmoothLink
									className='trace-resource-link'
									href={
										resource(
											selected.execution,
										)
											.href
									}>
									Open{' '}
									{
										resource(
											selected.execution,
										)
											.label
									}
									<ChevronRight
										size={
											13
										}
									/>
								</SmoothLink>
							</div>
						</div>
						<div
							className='trace-tabs'
							role='tablist'>
							{(
								[
									'lineage',
									'trace',
								] as Tab[]
							).map(item => (
								<button
									key={
										item
									}
									role='tab'
									aria-selected={
										tab ===
										item
									}
									className={
										tab ===
										item
											? 'active'
											: ''
									}
									onClick={() =>
										setTab(
											item,
										)
									}>
									{item ===
										'trace' && (
										<Activity
											size={
												14
											}
										/>
									)}
									{item ===
										'lineage' && (
										<GitBranch
											size={
												14
											}
										/>
									)}
									{item[0].toUpperCase() +
										item.slice(
											1,
										)}
								</button>
							))}
						</div>
						<div className='trace-tab-content'>
							{tab === 'lineage' && (
								<LineageView
									lineage={
										selected
									}
								/>
							)}
							{tab === 'trace' && (
								<TraceView
									lineage={
										selected
									}
								/>
							)}
						</div>
					</>
				) : (
					<div className='trace-detail-empty'>
						<Activity size={30} />
						<h2>Select an execution</h2>
						<p>
							Choose a run to inspect
							its lineage and
							execution trace.
						</p>
					</div>
				)}
			</section>
		</div>
	);
}

function LineageNode({
	link,
	direction,
}: {
	link: ArtifactLink;
	direction: 'input' | 'output';
}) {
	return (
		<div className={`lineage-node ${direction}`}>
			<span className='lineage-node-icon'>
				{direction === 'input' ? (
					<FileInput size={17} />
				) : (
					<Database size={17} />
				)}
			</span>
			<span>
				<small>{link.role}</small>
				<strong>{artifactLabel(link)}</strong>
				<code>{shortId(link.artifact.id)}</code>
			</span>
		</div>
	);
}

function LineageView({ lineage }: { lineage: ExecutionLineage }) {
	return (
		<div className='lineage-view'>
			<div className='lineage-stage'>
				<span>Inputs</span>
				<div>
					{lineage.inputs.map(link => (
						<LineageNode
							key={`${link.role}-${link.position}`}
							link={link}
							direction='input'
						/>
					))}
				</div>
			</div>
			<div className='lineage-connector'>
				<i />
				<ChevronRight size={17} />
			</div>
			<div className='lineage-execution'>
				<Activity size={20} />
				<small>Execution</small>
				<strong>{lineage.execution.kind}</strong>
				<code>{shortId(lineage.execution.id)}</code>
			</div>
			<div className='lineage-connector'>
				<i />
				<ChevronRight size={17} />
			</div>
			<div className='lineage-stage'>
				<span>Outputs</span>
				<div>
					{lineage.outputs.map(link => (
						<LineageNode
							key={`${link.role}-${link.position}`}
							link={link}
							direction='output'
						/>
					))}
				</div>
			</div>
		</div>
	);
}

function TraceView({ lineage }: { lineage: ExecutionLineage }) {
	const execution = lineage.execution;
	const events = [
		{
			label: 'Queued',
			time: execution.created_at,
			icon: <Clock3 size={15} />,
		},
		...(execution.started_at
			? [
					{
						label: 'Worker started',
						time: execution.started_at,
						icon: <ServerCog size={15} />,
					},
				]
			: []),
		...lineage.inputs.map(link => ({
			label: `Read ${link.role}`,
			time: execution.started_at ?? execution.created_at,
			icon: <FileInput size={15} />,
		})),
		...lineage.outputs.map(link => ({
			label: `Produced ${link.role}`,
			time:
				execution.completed_at ??
				execution.started_at ??
				execution.created_at,
			icon: <Box size={15} />,
		})),
		...(execution.completed_at
			? [
					{
						label: statusLabels[
							execution.status
						],
						time: execution.completed_at,
						icon:
							execution.status ===
							'completed' ? (
								<Check
									size={
										15
									}
								/>
							) : (
								<CircleAlert
									size={
										15
									}
								/>
							),
					},
				]
			: []),
	];
	return (
		<div className='trace-timeline'>
			<div className='trace-breakdown-title'>
				<div>
					<h3>Trace breakdown</h3>
					<p>
						Lifecycle and artifact events
						captured for this execution.
					</p>
				</div>
				<span>{events.length} events</span>
			</div>
			{events.map((event, index) => (
				<div
					className='trace-event'
					key={`${event.label}-${index}`}>
					<div className='trace-event-track'>
						<span>{event.icon}</span>
						{index < events.length - 1 && (
							<i />
						)}
					</div>
					<div>
						<strong>{event.label}</strong>
						<small>
							{formatDate(event.time)}
						</small>
					</div>
					<code>
						{index === 0
							? 'root'
							: `span-${index}`}
					</code>
				</div>
			))}
		</div>
	);
}
