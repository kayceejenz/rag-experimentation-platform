import { notFound } from 'next/navigation';
import { getServerSession } from 'next-auth/next';
import { ChatScreen } from '@/components/chat/chat-screen';
import { backendJson } from '@/lib/api/backend';
import { authOptions } from '@/lib/auth';
import type { Chat, Message, Project, Source } from '@/types/workspace';
import { ChatPageProps } from '@/types/chat-page';

export default async function ChatPage({
	params,
	searchParams,
}: ChatPageProps) {
	const session = await getServerSession(authOptions);
	if (!session?.user?.id) return null;
	const { chatId } = await params;
	const { prompt } = await searchParams;
	const chat = await backendJson<Chat>(session, `/chats/${chatId}`).catch(
		() => null,
	);
	if (!chat) notFound();
	const [messageResult, sourceResult, chatResult, projectResult] =
		await Promise.all([
			backendJson<{ messages: Message[] }>(
				session,
				`/chats/${chatId}/messages`,
			).catch(() => ({ messages: [] })),
			backendJson<{ sources: Source[] }>(
				session,
				`/knowledge-bases/${chat.knowledge_base_id}/sources`,
			).catch(() => ({ sources: [] })),
			backendJson<{ chats: Chat[] }>(
				session,
				`/projects/${chat.project_id}/chats`,
			).catch(() => ({ chats: [chat] })),
			backendJson<{ projects: Project[] }>(
				session,
				'/projects',
			).catch(() => ({ projects: [] })),
		]);
	return (
		<ChatScreen
			chat={chat}
			projectChats={chatResult.chats}
			initialMessages={messageResult.messages}
			initialSources={sourceResult.sources}
			initialPrompt={prompt?.slice(0, 12000)}
			projectName={
				projectResult.projects.find(
					project =>
						project.id === chat.project_id,
				)?.name ?? 'Current project'
			}
		/>
	);
}
