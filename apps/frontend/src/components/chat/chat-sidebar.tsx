'use client';

import { FormEvent, Dispatch, SetStateAction } from 'react';
import {
	ArrowLeft,
	Check,
	Ellipsis,
	MessageSquareText,
	PanelLeftClose,
	PanelLeftOpen,
	Plus,
	PencilLine,
	Trash,
	X,
	Folder,
} from 'lucide-react';
import type { Chat } from '@/types/workspace';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import { SmoothLink } from '@/components/navigation/smooth-link';

export function ChatSidebar({
	chat,
	chats,
	projectName,
	chatSidebarOpen,
	setChatSidebarOpen,
	menuChatId,
	setMenuChatId,
	editingChatId,
	setEditingChatId,
	deletingChatId,
	setDeletingChatId,
	chatActionBusy,
	onRename,
	onDelete,
	onCreateChat,
}: {
	chat: Chat;
	chats: Chat[];
	projectName: string;
	chatSidebarOpen: boolean;
	setChatSidebarOpen: Dispatch<SetStateAction<boolean>>;
	menuChatId: string | null;
	setMenuChatId: Dispatch<SetStateAction<string | null>>;
	editingChatId: string | null;
	setEditingChatId: Dispatch<SetStateAction<string | null>>;
	deletingChatId: string | null;
	setDeletingChatId: Dispatch<SetStateAction<string | null>>;
	chatActionBusy: boolean;
	onRename: (event: FormEvent<HTMLFormElement>, target: Chat) => void;
	onDelete: (target: Chat) => void;
	onCreateChat: () => void;
}) {
	return (
		<>
			<aside className='chat-history-sidebar'>
				<div className='chat-sidebar-brand'>
					<SmoothLink
						href='/'
						aria-label='Projects'>
						<strong className='editorial-brand-text'>
							kayceejenz.ai
						</strong>
					</SmoothLink>
					<button
						type='button'
						onClick={() =>
							setChatSidebarOpen(
								false,
							)
						}
						aria-label='Collapse chat sidebar'>
						<PanelLeftClose size={18} />
					</button>
				</div>
				<button
					className='new-chat-button'
					type='button'
					onClick={onCreateChat}
					disabled={chatActionBusy}>
					<Plus size={17} />
					<span>New chat</span>
				</button>
				<div className='chat-project-block'>
					<SmoothLink
						href={`/?project=${chat.project_id}`}>
						<Folder size={15} />
						<span>{projectName}</span>
					</SmoothLink>
				</div>
				<div className='chat-history-section'>
					<div className='chat-history-label'>
						Recent
					</div>
					<nav
						className='chat-history-list'
						aria-label='Chats'>
						{chats.map(item => (
							<div
								className={`history-chat-wrap ${item.id === chat.id ? 'active' : ''}`}
								key={item.id}>
								{editingChatId ===
								item.id ? (
									<form
										className='chat-rename-form'
										onSubmit={event =>
											onRename(
												event,
												item,
											)
										}>
										<input
											name='title'
											defaultValue={
												item.title
											}
											maxLength={
												240
											}
											autoFocus
											onKeyDown={event => {
												if (
													event.key ===
													'Escape'
												)
													setEditingChatId(
														null,
													);
											}}
										/>
										<button
											type='submit'
											disabled={
												chatActionBusy
											}>
											<Check
												size={
													14
												}
											/>
										</button>
										<button
											type='button'
											onClick={() =>
												setEditingChatId(
													null,
												)
											}>
											<X
												size={
													14
												}
											/>
										</button>
									</form>
								) : (
									<>
										<SmoothLink
											href={`/chats/${item.id}`}>
											<MessageSquareText
												size={
													14
												}
											/>
											<span>
												{
													item.title
												}
											</span>
										</SmoothLink>
										<button
											className='chat-options-trigger'
											type='button'
											onClick={() =>
												setMenuChatId(
													current =>
														current ===
														item.id
															? null
															: item.id,
												)
											}
											aria-label={`Options for ${item.title}`}>
											<Ellipsis
												size={
													15
												}
											/>
										</button>
										{menuChatId ===
											item.id && (
											<div className='chat-options-menu'>
												<button
													type='button'
													onClick={() => {
														setEditingChatId(
															item.id,
														);
														setMenuChatId(
															null,
														);
													}}>
													<PencilLine
														size={
															13
														}
													/>{' '}
													Rename
												</button>
												<button
													className='danger'
													type='button'
													onClick={() => {
														setDeletingChatId(
															item.id,
														);
														setMenuChatId(
															null,
														);
													}}>
													<Trash
														size={
															13
														}
													/>{' '}
													Delete
												</button>
											</div>
										)}
									</>
								)}
								{deletingChatId ===
									item.id && (
									<div className='chat-delete-confirm'>
										<p>
											Delete
											this
											chat?
										</p>
										<span>
											This
											cannot
											be
											undone.
										</span>
										<div>
											<button
												type='button'
												onClick={() =>
													setDeletingChatId(
														null,
													)
												}>
												Cancel
											</button>
											<button
												className='danger'
												type='button'
												disabled={
													chatActionBusy
												}
												onClick={() =>
													onDelete(
														item,
													)
												}>
												Delete
											</button>
										</div>
									</div>
								)}
							</div>
						))}
					</nav>
				</div>
				<div className='chat-sidebar-footer'>
					<SmoothLink
						href='/'
						className='chat-sidebar-projects'>
						<ArrowLeft size={14} /> Projects
					</SmoothLink>
					<ThemeToggle />
				</div>
			</aside>
			{!chatSidebarOpen && (
				<button
					className='chat-sidebar-reopen'
					type='button'
					onClick={() => setChatSidebarOpen(true)}
					aria-label='Open chat sidebar'>
					<PanelLeftOpen size={19} />
				</button>
			)}
		</>
	);
}
