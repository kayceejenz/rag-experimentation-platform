import { AppShell } from '@/components/layout/app-shell';
import { ProjectList } from '@/components/projects/project-list';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Project } from '@/types/workspace';

export default async function ProjectsPage() {
	const user = await getAuthUser();
	const projects = user
		? await backendJson<{ projects: Project[] }>(
				user.accessToken,
				'/projects',
			)
				.then(result => result.projects)
				.catch(() => [])
		: [];
	return (
		<AppShell
			user={
				user
					? {
							id: user.id,
							email: user.email,
							name: user.name,
						}
					: undefined
			}
			projects={projects}>
			<ProjectList initialProjects={projects} />
		</AppShell>
	);
}
