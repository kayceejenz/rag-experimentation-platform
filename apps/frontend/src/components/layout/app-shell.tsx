import { Menu } from 'lucide-react';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import { SignOutButton } from '@/components/layout/sign-out-button';
import { SessionSynchronizer } from '@/components/auth/session-synchronizer';
import { SmoothLink } from '@/components/navigation/smooth-link';
import { AppShellProps } from '@/types/app-shell';
import { WorkspaceNavigation } from '@/components/layout/workspace-navigation';

export function AppShell({
	title,
	description,
	actions,
	tabs,
	children,
	user,
	projects = [],
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
						<WorkspaceNavigation
							projects={projects}
							activeProjectId={
								activeProjectId
							}
							compact
						/>
					</div>
				</details>
				<WorkspaceNavigation
					projects={projects}
					activeProjectId={activeProjectId}
				/>

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
