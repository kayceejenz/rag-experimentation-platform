import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import {
	ProjectSectionMock,
	type ProjectSection,
} from '@/components/projects/project-section-mock';
import {
	IndexManager,
	type IndexCatalog,
} from '@/components/indexes/index-manager';
import { TraceExplorer } from '@/components/traces/trace-explorer';
import { ProjectSettings } from '@/components/projects/project-settings';
import { ProjectAccessDenied } from '@/components/projects/project-access-denied';
import { PromptManager } from '@/components/prompts/prompt-manager';
import { BenchmarkManager } from '@/components/benchmarks/benchmark-manager';
import { ExperimentManager, type ExperimentCatalog } from '@/components/experiments/experiment-manager';
import { AssistantManager, type AssistantCandidate } from '@/components/assistants/assistant-manager';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Execution, ExecutionLineage, ExperimentRun } from '@/types/trace';
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
type Props = { params: Promise<{ projectId: string; section: string }> };
export default async function ProjectSectionPage({ params }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId, section } = await params;
	if (!sections.has(section as ProjectSection)) notFound();
	const projects = await backendJson<{ projects: Project[] }>(
		user.accessToken,
		'/projects',
	)
		.then(value => value.projects)
		.catch(() => []);
	const project = projects.find(item => item.id === projectId);
	if (!project) notFound();
	const feature = section as 'indexes' | 'experiments' | 'benchmarks' | 'prompts' | 'assistants' | 'runs' | 'settings';
	if (project.role !== 'owner' && !project.permissions?.[feature]?.view) {
		return <AppShell user={{ id: user.id, email: user.email, name: user.name }} projects={projects} activeProjectId={projectId}><ProjectAccessDenied projectId={projectId} feature={feature}/></AppShell>;
	}
	if (section === 'indexes') {
		const [catalog, knowledgeBase] = await Promise.all([
			backendJson<IndexCatalog>(
				user.accessToken,
				`/projects/${projectId}/indexes`,
			),
			backendJson<KnowledgeBase>(
				user.accessToken,
				`/projects/${projectId}/source`,
			),
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
			<AppShell
				user={{
					id: user.id,
					email: user.email,
					name: user.name,
				}}
				projects={projects}
				activeProjectId={projectId}>
				<IndexManager
					project={project}
					knowledgeBase={knowledgeBase}
					folders={folders}
					sources={sources}
					initialCatalog={catalog}
				/>
			</AppShell>
		);
	}
	if (section === 'prompts') {
		const prompts=await backendJson<{prompts:PromptAsset[]}>(user.accessToken,`/projects/${projectId}/prompts`).then(value=>value.prompts);
		return <AppShell user={{id:user.id,email:user.email,name:user.name}} projects={projects} activeProjectId={projectId}><PromptManager project={project} initialPrompts={prompts}/></AppShell>;
	}
	if (section === 'benchmarks') {
		const datasets = await backendJson<{ datasets: BenchmarkDataset[] }>(
			user.accessToken,
			`/projects/${projectId}/benchmarks`,
		).then(value => value.datasets);
		return (
			<AppShell
				user={{ id: user.id, email: user.email, name: user.name }}
				projects={projects}
				activeProjectId={projectId}>
				<BenchmarkManager project={project} initialDatasets={datasets} />
			</AppShell>
		);
	}
	if (section === 'experiments') {
		const catalog=await backendJson<ExperimentCatalog>(user.accessToken,`/projects/${projectId}/experiments`);
		return <AppShell user={{id:user.id,email:user.email,name:user.name}} projects={projects} activeProjectId={projectId}><ExperimentManager project={project} initialCatalog={catalog}/></AppShell>;
	}
	if (section === 'assistants') {
		const [assistantResult, candidateResult] = await Promise.all([
			backendJson<{ assistants: Assistant[] }>(user.accessToken, `/projects/${projectId}/assistants`),
			backendJson<{ candidates: AssistantCandidate[] }>(user.accessToken, `/projects/${projectId}/assistant-candidates`),
		]);
		return <AppShell user={{ id: user.id, email: user.email, name: user.name }} projects={projects} activeProjectId={projectId}><AssistantManager project={project} initialAssistants={assistantResult.assistants} candidates={candidateResult.candidates}/></AppShell>;
	}
	if (section === 'runs') {
		const [executionResult, experimentRunResult, catalog, knowledgeBase] =
			await Promise.all([
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
		const initialLineage = executionResult.executions[0]
			? await backendJson<ExecutionLineage>(
					user.accessToken,
					`/projects/${projectId}/executions/${executionResult.executions[0].id}`,
				).catch(() => null)
			: null;
		return (
			<AppShell
				user={{
					id: user.id,
					email: user.email,
					name: user.name,
				}}
				projects={projects}
				activeProjectId={projectId}>
				<TraceExplorer
					project={project}
					initialExecutions={
						executionResult.executions
					}
					initialExperimentRuns={experimentRunResult.runs}
					initialLineage={initialLineage}
					resources={{
						sources,
						indexes: catalog.indexes.map(
							index => ({
								id: index.id,
								name: index
									.configuration
									.name,
							}),
						),
					}}
				/>
			</AppShell>
		);
	}
	if (section === 'settings') {
		const members = await backendJson<{ members: ProjectMember[] }>(user.accessToken, `/projects/${projectId}/members`).then(value => value.members).catch(() => []);
		return <AppShell user={{ id: user.id, email: user.email, name: user.name }} projects={projects} activeProjectId={projectId}><ProjectSettings project={project} initialMembers={members} currentUserId={user.id}/></AppShell>;
	}
	return (
		<AppShell
			user={{
				id: user.id,
				email: user.email,
				name: user.name,
			}}
			projects={projects}
			activeProjectId={projectId}>
			<ProjectSectionMock
				project={project}
				section={section as ProjectSection}
			/>
		</AppShell>
	);
}
