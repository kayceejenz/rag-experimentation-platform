import type { ReactNode } from 'react';
import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Project } from '@/types/workspace';

export default async function ProjectLayout({ children, params }: { children: ReactNode; params: Promise<{ projectId: string }> }) {
	const user = await getAuthUser();
	if (!user) return null;
	const { projectId } = await params;
	const projects = await backendJson<{ projects: Project[] }>(user.accessToken, '/projects')
		.then(value => value.projects)
		.catch(() => []);
	if (!projects.some(project => project.id === projectId)) notFound();
	return (
		<AppShell
			user={{ id: user.id, email: user.email, name: user.name }}
			projects={projects}
			activeProjectId={projectId}>
			{children}
		</AppShell>
	);
}
