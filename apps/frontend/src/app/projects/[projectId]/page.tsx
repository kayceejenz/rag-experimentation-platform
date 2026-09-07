import { notFound } from 'next/navigation';
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
	const project = await backendJson<Project>(user.accessToken, `/projects/${projectId}`).catch(() => null);
	if (!project) notFound();
	const experimentRuns = await backendJson<{ runs: ExperimentRun[] }>(
		user.accessToken,
		`/projects/${projectId}/experiments/runs`,
	).then(value => value.runs).catch(() => []);
	return <ProjectOverview project={project} experimentRuns={experimentRuns} />;
}
