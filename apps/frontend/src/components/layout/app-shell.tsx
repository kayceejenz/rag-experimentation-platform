import type { ReactNode } from 'react';
import { Folder, Menu, MessageSquareText, Plus, SquarePen } from 'lucide-react';
import type { Session } from 'next-auth';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import { SignOutButton } from '@/components/layout/sign-out-button';
import { SessionSynchronizer } from '@/components/auth/session-synchronizer';
import { SmoothLink } from '@/components/navigation/smooth-link';
import { AppShellProps } from '@/types/app-shell';

export function AppShell({
	title,
	description,
	actions,
	tabs,
	children,
	user,
	projects = [],
	chats = [],
	activeProjectId,
}: AppShellProps) {
	const initials = user?.name
		? user.name
				.split(' ')
				.map(w => w[0])
				.slice(0, 2)
				.join('')
				.toUpperCase()
		: (user?.email?.slice(0, 2).toUpperCase() ?? '?');

	return (
		<div className='app-shell'>
			<SessionSynchronizer />
			<aside className='rail' aria-label='Primary'>
				<SmoothLink
					href='/'
					className='rail-brand'
					aria-label='kayceejenz.ai'>
					<span className='rail-brand-text'>
						kayceejenz.ai
					</span>
				</SmoothLink>
				<details className='mobile-workspace-menu'>
					<summary aria-label='Open workspace navigation'>
						<Menu size={21} />
						<span>Menu</span>
					</summary>
					<div className='mobile-workspace-popover'>
						<SmoothLink href='/'>
							<SquarePen size={17} />
							<span>New chat</span>
						</SmoothLink>
						<div className='mobile-nav-label'>
							Projects
						</div>
						{projects.map(project => (
							<SmoothLink
								key={project.id}
								href={`/?project=${project.id}`}
								className={
									project.id ===
									activeProjectId
										? 'active'
										: ''
								}>
								<Folder
									size={
										16
									}
								/>
								<span>
									{
										project.name
									}
								</span>
							</SmoothLink>
						))}
						<SmoothLink href='/?newProject=1'>
							<Plus size={16} />
							<span>
								Create project
							</span>
						</SmoothLink>
						<div className='mobile-nav-label'>
							Recent chats
						</div>
						{chats.slice(0, 8).map(chat => (
							<SmoothLink
								key={chat.id}
								href={`/chats/${chat.id}`}>
								<MessageSquareText
									size={
										16
									}
								/>
								<span>
									{
										chat.title
									}
								</span>
							</SmoothLink>
						))}
					</div>
				</details>
				<nav className='app-navigation'>
					<SmoothLink href='/' className='active'>
						<SquarePen size={17} />
						<span>Chat</span>
					</SmoothLink>
				</nav>
				<div className='rail-projects'>
					<div className='rail-projects-heading'>
						<span>Projects</span>
						<SmoothLink
							href='/?newProject=1'
							aria-label='Create project'>
							<Plus size={14} />
						</SmoothLink>
					</div>
					<div className='rail-project-list'>
						{projects.map(project => (
							<SmoothLink
								key={project.id}
								href={`/?project=${project.id}`}
								className={
									project.id ===
									activeProjectId
										? 'active'
										: ''
								}>
								<Folder
									size={
										15
									}
								/>
								<span>
									{
										project.name
									}
								</span>
							</SmoothLink>
						))}
						{projects.length === 0 && (
							<p>No projects yet</p>
						)}
					</div>
				</div>

				<div className='rail-chats'>
					<div className='rail-section-heading'>
						<span>Recent chats</span>
					</div>
					<nav
						className='rail-chat-list'
						aria-label='Recent chats'>
						{chats.map(chat => (
							<SmoothLink
								key={chat.id}
								href={`/chats/${chat.id}`}>
								<MessageSquareText
									size={
										16
									}
								/>
								<span>
									{
										chat.title
									}
								</span>
							</SmoothLink>
						))}
						{chats.length === 0 && (
							<p>No chats yet</p>
						)}
					</nav>
				</div>

				<div className='rail-footer'>
					<ThemeToggle />
					{user && (
						<div className='rail-user'>
							<div className='rail-user-avatar'>
								{user.image ? (
									// eslint-disable-next-line @next/next/no-img-element
									<img
										src={
											user.image
										}
										alt={
											user.name ??
											'User'
										}
									/>
								) : (
									<span>
										{
											initials
										}
									</span>
								)}
							</div>

							<div className='rail-user-info'>
								<span className='rail-user-name'>
									{user.name ??
										user.email}
								</span>
								<span className='rail-user-role'>
									Workspace
								</span>
							</div>
							<SignOutButton />
						</div>
					)}
				</div>
			</aside>

			<main className='workspace'>
				{(title || description || actions) && (
					<header className='workspace-header'>
						<div>
							{title && (
								<h1>{title}</h1>
							)}
							{description && (
								<p>
									{
										description
									}
								</p>
							)}
						</div>
						{actions ? (
							<div className='workspace-actions'>
								{actions}
							</div>
						) : null}
					</header>
				)}
				{tabs ? (
					<div className='workspace-tabs'>
						{tabs}
					</div>
				) : null}
				{children}
			</main>
		</div>
	);
}
