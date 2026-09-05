import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { ProjectOverview } from '@/components/projects/project-overview';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Project } from '@/types/workspace';
import type { ExperimentRun } from '@/types/trace';

type Props = { params: Promise<{ projectId: string }> };
export default async function ProjectPage({ params }: Props) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId } = await params;
	const projects = await backendJson<{ projects: Project[] }>(
		user.accessToken,
		'/projects',
	)
		.then(value => value.projects)
		.catch(() => []);
	const project = projects.find(item => item.id === projectId);
	if (!project) notFound();
	const experimentRuns = await backendJson<{ runs: ExperimentRun[] }>(
		user.accessToken,
		`/projects/${projectId}/experiments/runs`,
	).then(value => value.runs).catch(() => []);
	return (
		<AppShell
			user={{
				id: user.id,
				email: user.email,
				name: user.name,
			}}
			projects={projects}
			activeProjectId={projectId}>
			<ProjectOverview project={project} experimentRuns={experimentRuns} />
		</AppShell>
	);
}
