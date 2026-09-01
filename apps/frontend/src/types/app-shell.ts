import { ReactNode } from 'react';
import { Chat, Project } from './workspace';

export type AppShellUser = {
	id: string;
	email?: string | null;
	name?: string | null;
	image?: string | null;
};

export type AppShellProps = {
	title?: string;
	description?: string;
	actions?: ReactNode;
	tabs?: ReactNode;
	children: ReactNode;
	user?: AppShellUser;
	projects?: Project[];
	chats?: Chat[];
	activeProjectId?: string | null;
	activeNavigation?: 'bots' | 'traces';
};
