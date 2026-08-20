import { notFound } from 'next/navigation';
import { ChatScreen } from '@/components/chat/chat-screen';
import { getAuthUser } from '@/lib/api/auth';
import { backendJson } from '@/lib/api/backend';
import type { Chat, Message, Project, Source } from '@/types/workspace';
import { ChatPageProps } from '@/types/chat-page';

export default async function ChatPage({
	params,
	searchParams,
}: ChatPageProps) {
	const user = await getAuthUser();
	if (!user) return null;

	const [{ chatId }, { prompt }] = await Promise.all([
		params,
		searchParams,
	]);

	const [chat, projectsResult] = await Promise.all([
		backendJson<Chat>(user.accessToken, `/chats/${chatId}`).catch(
			() => null,
		),
		backendJson<{ projects: Project[] }>(
			user.accessToken,
			'/projects',
		).catch(() => ({ projects: [] })),
	]);

	if (!chat) notFound();

	const [messageResult, sourceResult, chatResult] = await Promise.all([
		backendJson<{ messages: Message[] }>(
			user.accessToken,
			`/chats/${chatId}/messages`,
		).catch(() => ({ messages: [] })),
		backendJson<{ sources: Source[] }>(
			user.accessToken,
			`/knowledge-bases/${chat.knowledge_base_id}/sources`,
		).catch(() => ({ sources: [] })),
		backendJson<{ chats: Chat[] }>(
			user.accessToken,
			`/projects/${chat.project_id}/chats`,
		).catch(() => ({ chats: [chat] })),
	]);

	const projectName =
		projectsResult.projects.find(
			project => project.id === chat.project_id,
		)?.name ?? 'Current project';
	return (
		<ChatScreen
			chat={chat}
			projectChats={chatResult.chats}
			initialMessages={messageResult.messages}
			initialSources={sourceResult.sources}
			initialPrompt={prompt?.slice(0, 12000)}
			projectName={projectName}
		/>
	);
}
