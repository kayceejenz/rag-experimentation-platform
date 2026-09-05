import {
	Bot,
	Box,
	Braces,
	CheckCircle2,
	FlaskConical,
	GitBranch,
	Layers3,
} from 'lucide-react';
import { formatDateTime } from '@/lib/format';

export type AssistantLineageData = {
	assistant: { id: string; name: string };
	revision: {
		id: string;
		version: number;
		created_at: string;
		configuration: {
			retrieval?: Record<string, unknown>;
			generation?: Record<string, unknown>;
		};
	};
	experiment: { id: string; name: string; hypothesis: string };
	run: {
		id: string;
		variant_run_id: string;
		code_revision: string;
		created_at: string;
		completed_at: string;
		metrics: Record<string, number>;
	};
	variant: { id: string; name: string; configuration_hash: string };
	index: {
		id: string;
		configuration: {
			name?: string;
			embedding?: { model?: string };
			chunking?: { strategy?: string };
		};
	};
	system_prompt: { version_id: string; name: string; version: number };
	rag_prompt: { version_id: string; name: string; version: number };
};

export function AssistantLineage({
	lineage,
}: {
	lineage: AssistantLineageData;
}) {
	const nodes = [
		{
			label: 'Experiment',
			value: lineage.experiment.name,
			detail: lineage.experiment.hypothesis,
			icon: FlaskConical,
		},
		{
			label: 'Completed run',
			value: lineage.variant.name,
			detail: formatDateTime(lineage.run.completed_at),
			icon: CheckCircle2,
		},
		{
			label: 'Assistant revision',
			value: `v${lineage.revision.version}`,
			detail: lineage.variant.configuration_hash.slice(0, 12),
			icon: GitBranch,
		},
		{
			label: 'Assistant',
			value: lineage.assistant.name,
			detail: 'Active configuration',
			icon: Bot,
		},
	];
	return (
		<div className='assistant-lineage-page'>
			<section
				className='assistant-lineage-flow'
				aria-label='Assistant lineage flow'>
				{nodes.map(
					(
						{
							label,
							value,
							detail,
							icon: Icon,
						},
						index,
					) => (
						<article
							className='assistant-lineage-step'
							key={label}>
							<header>
								<span className='lineage-step-icon'>
									<Icon
										size={
											15
										}
									/>
								</span>
								<span className='lineage-step-number'>
									{String(
										index +
											1,
									).padStart(
										2,
										'0',
									)}
								</span>
							</header>
							<small>{label}</small>
							<strong>{value}</strong>
							<p>{detail}</p>
						</article>
					),
				)}
			</section>
			<div className='assistant-lineage-grid'>
				<LineageTable
					title='Bound assets'
					icon={Box}
					rows={[
						[
							'Vector index',
							lineage.index
								.configuration
								.name ||
								lineage.index
									.id,
						],
						[
							'Embedding model',
							lineage.index
								.configuration
								.embedding
								?.model ||
								'Configured index model',
						],
						[
							'Chunking strategy',
							lineage.index
								.configuration
								.chunking
								?.strategy ||
								'Configured index strategy',
						],
						[
							'System prompt',
							`${lineage.system_prompt.name} · v${lineage.system_prompt.version}`,
						],
						[
							'RAG prompt',
							`${lineage.rag_prompt.name} · v${lineage.rag_prompt.version}`,
						],
					]}
				/>
				<LineageTable
					title='Provenance'
					icon={Braces}
					rows={[
						[
							'Experiment run',
							lineage.run.id,
						],
						[
							'Variant run',
							lineage.run
								.variant_run_id,
						],
						[
							'Code revision',
							lineage.run
								.code_revision ||
								'development',
						],
						[
							'Configuration',
							lineage.variant
								.configuration_hash,
						],
						[
							'Promoted',
							formatDateTime(
								lineage.revision
									.created_at,
							),
						],
					]}
					monospace
				/>
			</div>
			<section className='assistant-lineage-config'>
				<header>
					<Layers3 size={16} />
					<div>
						<h2>Run configuration</h2>
						<p>
							The immutable retrieval
							and generation settings
							promoted into this
							revision.
						</p>
					</div>
				</header>
				<div>
					<ConfigTable
						title='Retrieval'
						values={
							lineage.revision
								.configuration
								.retrieval
						}
					/>
					<ConfigTable
						title='Generation'
						values={
							lineage.revision
								.configuration
								.generation
						}
					/>
				</div>
			</section>
		</div>
	);
}

function LineageTable({
	title,
	icon: Icon,
	rows,
	monospace = false,
}: {
	title: string;
	icon: typeof Box;
	rows: string[][];
	monospace?: boolean;
}) {
	return (
		<section className='assistant-lineage-table'>
			<header>
				<Icon size={15} />
				<h2>{title}</h2>
			</header>
			<table>
				<tbody>
					{rows.map(([label, value]) => (
						<tr key={label}>
							<th>{label}</th>
							<td
								className={
									monospace
										? 'lineage-code'
										: ''
								}>
								{value}
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</section>
	);
}

function ConfigTable({
	title,
	values = {},
}: {
	title: string;
	values?: Record<string, unknown>;
}) {
	return (
		<section>
			<h3>{title}</h3>
			<table>
				<tbody>
					{Object.entries(values).map(
						([key, value]) => (
							<tr key={key}>
								<th>
									{key.replaceAll(
										'_',
										' ',
									)}
								</th>
								<td>
									{String(
										value,
									)}
								</td>
							</tr>
						),
					)}
				</tbody>
			</table>
		</section>
	);
}
