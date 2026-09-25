import { notFound } from 'next/navigation';
import {
	ProjectSectionMock,
	type ProjectSection,
} from '@/components/projects/project-section-mock';
import {
	IndexManager,
	type IndexCatalog,
} from '@/components/indexes/index-manager';
import type { IndexDetail } from '@/components/indexes/index-types';
import { TraceExplorer } from '@/components/traces/trace-explorer';
import { ProjectSettings } from '@/components/projects/project-settings';
import { ProjectAccessDenied } from '@/components/projects/project-access-denied';
import {
	PromptManager,
	type PromptDetail,
} from '@/components/prompts/prompt-manager';
import {
	BenchmarkManager,
	type BenchmarkDetail,
} from '@/components/benchmarks/benchmark-manager';
import {
	ExperimentManager,
	type ExperimentCatalog,
	type ExperimentDetail,
	type ExperimentRunDetail,
} from '@/components/experiments/experiment-manager';
import {
	AssistantManager,
	type AssistantCandidate,
} from '@/components/assistants/assistant-manager';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Execution, ExperimentRun } from '@/types/trace';
import type {
	KnowledgeBase,
	BenchmarkDataset,
	KnowledgeFolder,
	Assistant,
	Project,
	ProjectMember,
	PromptAsset,
	Source,
} from '@/types/workspace';

const sections = new Set<ProjectSection>([
	'indexes',
	'experiments',
	'benchmarks',
	'assistants',
	'prompts',
	'runs',
	'settings',
]);

type Props = {
	params: Promise<{ projectId: string; section: string }>;
	searchParams: Promise<{
		index?: string;
		prompt?: string;
		benchmark?: string;
		experiment?: string;
		run?: string;
	}>;
};

export default async function ProjectSectionPage({ params, searchParams }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId, section } = await params;
	const query = await searchParams;
	if (!sections.has(section as ProjectSection)) notFound();
	const project = await backendJson<Project>(
		user.accessToken,
		`/projects/${projectId}`,
	).catch(() => null);
	if (!project) notFound();
	const feature = section as
		| 'indexes'
		| 'experiments'
		| 'benchmarks'
		| 'prompts'
		| 'assistants'
		| 'runs'
		| 'settings';
	if (project.role !== 'owner' && !project.permissions?.[feature]?.view) {
		return (
			<ProjectAccessDenied
				projectId={projectId}
				feature={feature}
			/>
		);
	}
	if (section === 'indexes') {
		const [catalog, knowledgeBase, initialDetail] = await Promise.all([
			backendJson<IndexCatalog>(
				user.accessToken,
				`/projects/${projectId}/indexes`,
			),
			backendJson<KnowledgeBase>(
				user.accessToken,
				`/projects/${projectId}/source`,
			),
			query.index
				? backendJson<IndexDetail>(
						user.accessToken,
						`/projects/${projectId}/indexes/${query.index}`,
					).catch(() => null)
				: Promise.resolve(null),
		]);
		const [folders, sources] = await Promise.all([
			backendJson<{ folders: KnowledgeFolder[] }>(
				user.accessToken,
				`/knowledge-bases/${knowledgeBase.id}/folders`,
			)
				.then(value => value.folders)
				.catch(() => []),
			backendJson<{ sources: Source[] }>(
				user.accessToken,
				`/knowledge-bases/${knowledgeBase.id}/sources`,
			)
				.then(value => value.sources)
				.catch(() => []),
		]);
		return (
			<IndexManager
				project={project}
				knowledgeBase={knowledgeBase}
				folders={folders}
				sources={sources}
				initialCatalog={catalog}
				initialDetail={initialDetail}
			/>
		);
	}
	if (section === 'prompts') {
		const [prompts, initialDetail] = await Promise.all([
			backendJson<{ prompts: PromptAsset[] }>(
				user.accessToken,
				`/projects/${projectId}/prompts`,
			).then(value => value.prompts),
			query.prompt
				? backendJson<PromptDetail>(
						user.accessToken,
						`/projects/${projectId}/prompts/${query.prompt}`,
					).catch(() => null)
				: Promise.resolve(null),
		]);
		return (
			<PromptManager
				project={project}
				initialPrompts={prompts}
				initialDetail={initialDetail}
			/>
		);
	}
	if (section === 'benchmarks') {
		const [datasets, initialDetail] = await Promise.all([
			backendJson<{ datasets: BenchmarkDataset[] }>(
				user.accessToken,
				`/projects/${projectId}/benchmarks`,
			).then(value => value.datasets),
			query.benchmark
				? backendJson<BenchmarkDetail>(
						user.accessToken,
						`/projects/${projectId}/benchmarks/${query.benchmark}`,
					).catch(() => null)
				: Promise.resolve(null),
		]);
		return (
			<BenchmarkManager
				project={project}
				initialDatasets={datasets}
				initialDetail={initialDetail}
			/>
		);
	}
	if (section === 'experiments') {
		const [catalog, initialDetail] = await Promise.all([
			backendJson<ExperimentCatalog>(
				user.accessToken,
				`/projects/${projectId}/experiments`,
			),
			query.experiment
				? backendJson<ExperimentDetail>(
						user.accessToken,
						`/projects/${projectId}/experiments/${query.experiment}`,
					).catch(() => null)
				: Promise.resolve(null),
		]);
		const initialRunDetail =
			query.run && initialDetail
				? await backendJson<ExperimentRunDetail>(
						user.accessToken,
						`/projects/${projectId}/experiments/${initialDetail.experiment.id}/runs/${query.run}`,
					).catch(() => null)
				: null;
		return (
			<ExperimentManager
				project={project}
				initialCatalog={catalog}
				initialDetail={initialDetail}
				initialRunDetail={initialRunDetail}
			/>
		);
	}
	if (section === 'assistants') {
		const [assistantResult, candidateResult] = await Promise.all([
			backendJson<{ assistants: Assistant[] }>(
				user.accessToken,
				`/projects/${projectId}/assistants`,
			),
			backendJson<{ candidates: AssistantCandidate[] }>(
				user.accessToken,
				`/projects/${projectId}/assistant-candidates`,
			),
		]);
		return (
			<AssistantManager
				project={project}
				initialAssistants={assistantResult.assistants}
				candidates={candidateResult.candidates}
			/>
		);
	}
	if (section === 'runs') {
		const [
			executionResult,
			experimentRunResult,
			catalog,
			knowledgeBase,
		] = await Promise.all([
			backendJson<{ executions: Execution[] }>(
				user.accessToken,
				`/projects/${projectId}/executions?limit=100`,
			).catch(() => ({ executions: [] })),
			backendJson<{ runs: ExperimentRun[] }>(
				user.accessToken,
				`/projects/${projectId}/experiments/runs`,
			).catch(() => ({ runs: [] })),
			backendJson<IndexCatalog>(
				user.accessToken,
				`/projects/${projectId}/indexes`,
			).catch(() => ({
				embedding_models: [],
				chunking_strategies: [],
				indexes: [],
			})),
			backendJson<KnowledgeBase>(
				user.accessToken,
				`/projects/${projectId}/source`,
			).catch(() => null),
		]);
		const sources = knowledgeBase
			? await backendJson<{ sources: Source[] }>(
					user.accessToken,
					`/knowledge-bases/${knowledgeBase.id}/sources`,
				)
					.then(value => value.sources)
					.catch(() => [])
			: [];
		return (
			<TraceExplorer
				project={project}
				initialExecutions={executionResult.executions}
				initialExperimentRuns={experimentRunResult.runs}
				initialLineage={null}
				resources={{
					sources,
					indexes: catalog.indexes.map(index => ({
						id: index.id,
						name: index.configuration.name,
					})),
				}}
			/>
		);
	}
	if (section === 'settings') {
		const members = await backendJson<{ members: ProjectMember[] }>(
			user.accessToken,
			`/projects/${projectId}/members`,
		)
			.then(value => value.members)
			.catch(() => []);
		return (
			<ProjectSettings
				project={project}
				initialMembers={members}
				currentUserId={user.id}
			/>
		);
	}
	return (
		<ProjectSectionMock
			project={project}
			section={section as ProjectSection}
		/>
	);
}
