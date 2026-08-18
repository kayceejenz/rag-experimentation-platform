export type ChatPageProps = {
	params: Promise<{ chatId: string }>;
	searchParams: Promise<{ prompt?: string }>;
};
