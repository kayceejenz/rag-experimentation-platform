import { AppShell } from '@/components/layout/app-shell';
import { ProjectWorkspace } from '@/components/workspace/project-workspace';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Chat, Project } from '@/types/workspace';
import { PageProps } from '@/types/page';

export default async function Home({ searchParams }: PageProps) {
	const user = await getAuthUser();
	const query = await searchParams;

	const projects = user
		? await backendJson<{ projects: Project[] }>(
				user.accessToken,
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
	const chats = user
		? (
				await Promise.all(
					projects.map(project =>
						backendJson<{ chats: Chat[] }>(
							user.accessToken,
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
			user={user ? { id: user.id, email: user.email, name: user.name } : undefined}
			projects={projects}
			chats={chats}
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
