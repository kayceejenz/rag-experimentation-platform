import { Session } from 'next-auth';
import { ReactNode } from 'react';
import { Chat, Project } from './workspace';

export type AppShellProps = {
	title?: string;
	description?: string;
	actions?: ReactNode;
	tabs?: ReactNode;
	children: ReactNode;
	user?: Session['user'];
	projects?: Project[];
	chats?: Chat[];
	activeProjectId?: string | null;
	session?: Session | null;
};
