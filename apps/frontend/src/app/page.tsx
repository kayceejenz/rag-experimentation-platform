import { AppShell } from '@/components/layout/app-shell';
import { ProjectWorkspace } from '@/components/workspace/project-workspace';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { backendJson } from '@/lib/api/backend';
import type { Chat, Project } from '@/types/workspace';
import { PageProps } from '@/types/page';

export default async function Home({ searchParams }: PageProps) {
	const session = await getServerSession(authOptions);
	const query = await searchParams;

	const projects = session?.user?.id
		? await backendJson<{ projects: Project[] }>(
				session,
				'/projects',
			)
				.then(result => result.projects)
				.catch(() => [])
		: [];

	const selectedProjectId = projects.some(
		project => project.id === query.project,
	)
		? query.project!
		: (projects[0]?.id ?? null);
	const chats = session?.user?.id
		? (
				await Promise.all(
					projects.map(project =>
						backendJson<{ chats: Chat[] }>(
							session,
							`/projects/${project.id}/chats`,
						)
							.then(
								result =>
									result.chats,
							)
							.catch(() => []),
					),
				)
			)
				.flat()
				.sort(
					(left, right) =>
						new Date(
							right.updated_at,
						).getTime() -
						new Date(
							left.updated_at,
						).getTime(),
				)
				.slice(0, 12)
		: [];
	return (
		<AppShell
			user={session?.user}
			projects={projects}
			chats={chats}
			session={session}
			activeProjectId={selectedProjectId}>
			<ProjectWorkspace
				key={`${selectedProjectId ?? 'none'}-${query.newProject ?? 'closed'}`}
				initialProjects={projects}
				initialSelectedId={selectedProjectId}
				initialShowProjectForm={
					query.newProject === '1'
				}
			/>
		</AppShell>
	);
}
