import {
	ArrowUpRight,
	Bot,
	CircleDot,
	Database,
	FlaskConical,
	Gauge,
	Layers3,
	PlayCircle,
	Plus,
	Settings,
} from 'lucide-react';
import type { Project } from '@/types/workspace';

const definitions = {
	indexes: {
		title: 'Indexes',
		eyebrow: 'Data',
		description:
			'Immutable vector indexes derived from governed chunk datasets.',
		icon: Layers3,
		action: 'Create index',
		columns: [
			'Index',
			'Embedding',
			'Chunk dataset',
			'Status',
			'Created',
		],
		rows: [
			[
				'support-gemini-v1',
				'gemini-embedding-001',
				'support-chunks-v3',
				'Ready',
				'Today',
			],
			[
				'policies-gemini-v2',
				'gemini-embedding-001',
				'policy-chunks-v2',
				'Building',
				'Yesterday',
			],
		],
	},
	experiments: {
		title: 'Experiments',
		eyebrow: 'Development',
		description:
			'Compare retrieval and generation configurations without overwriting history.',
		icon: FlaskConical,
		action: 'New experiment',
		columns: [
			'Experiment',
			'Runs',
			'Best score',
			'Owner',
			'Updated',
		],
		rows: [
			[
				'Retrieval baseline',
				'8',
				'0.87',
				'Workspace owner',
				'Today',
			],
			[
				'Chunk strategy comparison',
				'4',
				'0.81',
				'Workspace owner',
				'Yesterday',
			],
		],
	},
	benchmarks: {
		title: 'Benchmarks',
		eyebrow: 'Development',
		description:
			'Versioned golden datasets used for repeatable evaluation.',
		icon: Gauge,
		action: 'New benchmark',
		columns: [
			'Dataset',
			'Version',
			'Examples',
			'Last evaluation',
			'Status',
		],
		rows: [
			['Support golden set', 'v3', '120', 'Today', 'Ready'],
			['Policy questions', 'v1', '48', 'Yesterday', 'Draft'],
		],
	},
	assistants: {
		title: 'Assistants',
		eyebrow: 'AI applications',
		description:
			'Deployable RAG applications bound to explicit configuration revisions.',
		icon: Bot,
		action: 'Create assistant',
		columns: [
			'Assistant',
			'Active revision',
			'Index',
			'Environment',
			'Status',
		],
		rows: [
			[
				'Customer support',
				'v4',
				'support-gemini-v1',
				'Production',
				'Active',
			],
			[
				'Policy copilot',
				'v2',
				'policies-gemini-v2',
				'Development',
				'Draft',
			],
		],
	},
	runs: {
		title: 'Runs',
		eyebrow: 'Operations',
		description:
			'Project-wide execution history for pipelines, indexes, experiments, evaluations, and inference.',
		icon: PlayCircle,
		action: 'Refresh',
		columns: ['Run', 'Type', 'Resource', 'Duration', 'Status'],
		rows: [
			[
				'run_8fa2',
				'Index build',
				'support-gemini-v1',
				'2m 14s',
				'Completed',
			],
			[
				'run_7bc1',
				'Chunking',
				'Knowledge',
				'48s',
				'Completed',
			],
			[
				'run_638d',
				'Evaluation',
				'Retrieval baseline',
				'—',
				'Running',
			],
		],
	},
	settings: {
		title: 'Project settings',
		eyebrow: 'Settings',
		description:
			'Project details, access, defaults, and lifecycle controls.',
		icon: Settings,
		action: 'Save changes',
		columns: ['Setting', 'Value', 'Scope', 'Updated', ''],
		rows: [
			[
				'Default embedding',
				'gemini-embedding-001',
				'Project',
				'Today',
				'',
			],
			[
				'Run retention',
				'30 days',
				'Project',
				'Yesterday',
				'',
			],
		],
	},
} as const;

export type ProjectSection = keyof typeof definitions;
export function ProjectSectionMock({
	project,
	section,
}: {
	project: Project;
	section: ProjectSection;
}) {
	const definition = definitions[section];
	const Icon = definition.icon;
	return (
		<div className='catalog-page'>
			<header className='product-page-header'>
				<div>
					<span className='eyebrow'>
						{definition.eyebrow}
					</span>
					<h1>{definition.title}</h1>
					<p>{definition.description}</p>
				</div>
				<button className='primary-action'>
					<Plus size={15} />
					{definition.action}
				</button>
			</header>
			<div className='catalog-context'>
				<span>
					<Icon size={17} />
				</span>
				<div>
					<small>Project</small>
					<strong>{project.name}</strong>
				</div>
			</div>
			<section className='catalog-table-panel'>
				<header>
					<div>
						<h2>{definition.title}</h2>
						<p>
							Frontend structure
							preview · data is mocked
							for layout review.
						</p>
					</div>
					<label>
						<Database size={14} />
						<input
							placeholder={`Search ${definition.title.toLowerCase()}`}
						/>
					</label>
				</header>
				<div className='catalog-table-wrap'>
					<table>
						<thead>
							<tr>
								{definition.columns.map(
									column => (
										<th
											key={
												column
											}>
											{
												column
											}
										</th>
									),
								)}
							</tr>
						</thead>
						<tbody>
							{definition.rows.map(
								row => (
									<tr
										key={
											row[0]
										}>
										{row.map(
											(
												value,
												cell,
											) => (
												<td
													key={`${value}-${cell}`}>
													{cell ===
													0 ? (
														<span className='catalog-primary'>
															<CircleDot
																size={
																	13
																}
															/>
															<strong>
																{
																	value
																}
															</strong>
														</span>
													) : cell ===
															row.length -
																1 &&
													  value ? (
														<span
															className={`catalog-state ${String(value).toLowerCase()}`}>
															{
																value
															}
														</span>
													) : (
														value
													)}
												</td>
											),
										)}
										<td className='catalog-open'>
											<ArrowUpRight
												size={
													14
												}
											/>
										</td>
									</tr>
								),
							)}
						</tbody>
					</table>
				</div>
			</section>
		</div>
	);
}
