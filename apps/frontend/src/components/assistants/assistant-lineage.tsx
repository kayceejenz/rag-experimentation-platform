import {
	Bot,
	Box,
	Braces,
	CheckCircle2,
	ClipboardCheck,
	ExternalLink,
	FlaskConical,
	GitBranch,
	Layers3,
	MessageSquareText,
} from 'lucide-react';
import { formatDateTime } from '@/lib/format';
import { SmoothLink } from '@/components/navigation/smooth-link';

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
	experiment: {
		id: string;
		name: string;
		hypothesis: string;
		benchmark_id: string;
		benchmark_name: string;
		benchmark_version: number;
	};
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
	system_prompt: {
		id: string;
		version_id: string;
		name: string;
		version: number;
	};
	rag_prompt: {
		id: string;
		version_id: string;
		name: string;
		version: number;
	};
};

export function AssistantLineage({
	lineage,
	projectId,
}: {
	lineage: AssistantLineageData;
	projectId: string;
}) {
	const projectBase = `/projects/${projectId}`;
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
				{nodes.map(({ label, value, detail, icon: Icon }, index) => (
					<article
						className='assistant-lineage-step'
						key={label}>
						<header>
							<span className='lineage-step-icon'>
								<Icon size={15} />
							</span>
							<span className='lineage-step-number'>
								{String(index + 1).padStart(2, '0')}
							</span>
						</header>
						<small>{label}</small>
						<strong>{value}</strong>
						<p>{detail}</p>
					</article>
				))}
			</section>
			<div className='assistant-lineage-grid'>
				<LineageTable
					title='Index configuration'
					icon={Box}
					href={`${projectBase}/indexes?index=${lineage.index.id}`}
					linkLabel='Open index configuration'
					rows={[
						{
							label: 'Vector index',
							value:
								lineage.index.configuration.name ||
								lineage.index.id,
						},
						{
							label: 'Embedding model',
							value:
								lineage.index.configuration.embedding?.model ||
								'Configured index model',
						},
						{
							label: 'Chunking strategy',
							value:
								lineage.index.configuration.chunking?.strategy ||
								'Configured index strategy',
						},
					]}
				/>
				<LineageTable
					title='System prompt'
					icon={MessageSquareText}
					href={`${projectBase}/prompts?prompt=${lineage.system_prompt.id}`}
					linkLabel='Open system prompt'
					rows={[
						{
							label: 'Prompt',
							value: lineage.system_prompt.name,
						},
						{
							label: 'Version',
							value: `v${lineage.system_prompt.version}`,
						},
					]}
				/>
				<LineageTable
					title='RAG prompt'
					icon={MessageSquareText}
					href={`${projectBase}/prompts?prompt=${lineage.rag_prompt.id}`}
					linkLabel='Open RAG prompt'
					rows={[
						{ label: 'Prompt', value: lineage.rag_prompt.name },
						{
							label: 'Version',
							value: `v${lineage.rag_prompt.version}`,
						},
					]}
				/>
				<LineageTable
					title='Benchmark'
					icon={ClipboardCheck}
					href={`${projectBase}/benchmarks?benchmark=${lineage.experiment.benchmark_id}`}
					linkLabel='Open benchmark'
					rows={[
						{
							label: 'Dataset',
							value: lineage.experiment.benchmark_name,
						},
						{
							label: 'Version',
							value: `v${lineage.experiment.benchmark_version}`,
						},
					]}
				/>
				<LineageTable
					title='Provenance'
					icon={Braces}
					href={`${projectBase}/experiments?experiment=${lineage.experiment.id}&run=${lineage.run.id}`}
					linkLabel='Open experiment run'
					rows={[
						{ label: 'Experiment run', value: lineage.run.id },
						{
							label: 'Variant run',
							value: lineage.run.variant_run_id,
						},
						{
							label: 'Code revision',
							value: lineage.run.code_revision || 'development',
						},
						{
							label: 'Configuration',
							value: lineage.variant.configuration_hash,
						},
						{
							label: 'Promoted',
							value: formatDateTime(lineage.revision.created_at),
						},
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
					<RecordLink
						href={`${projectBase}/experiments?experiment=${lineage.experiment.id}&run=${lineage.run.id}`}
						label='Open source run configuration'
					/>
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
	href,
	linkLabel,
	rows,
	monospace = false,
}: {
	title: string;
	icon: typeof Box;
	href: string;
	linkLabel: string;
	rows: Array<{ label: string; value: string }>;
	monospace?: boolean;
}) {
	return (
		<section className='assistant-lineage-table'>
			<header>
				<Icon size={15} />
				<h2>{title}</h2>
				<RecordLink href={href} label={linkLabel} />
			</header>
			<table>
				<tbody>
					{rows.map(({ label, value }) => (
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

function RecordLink({ href, label }: { href: string; label: string }) {
	return (
		<SmoothLink
			className='lineage-record-link'
			href={href}
			aria-label={label}
			title={label}>
			<ExternalLink size={13} />
		</SmoothLink>
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
