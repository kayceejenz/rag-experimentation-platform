import { Chat, Message, Source } from './workspace';

export type ChatScreenProps = {
	chat: Chat;
	projectChats: Chat[];
	initialMessages: Message[];
	initialSources: Source[];
	initialPrompt?: string;
	projectName: string;
};
