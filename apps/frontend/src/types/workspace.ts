export type Project = {
	id: string;
	owner_id: string;
	name: string;
	description: string | null;
	role: string;
	created_at: string;
	updated_at: string;
};

export type Chat = {
	id: string;
	bot_id: string;
	project_id: string;
	created_by: string;
	knowledge_base_id: string;
	title: string;
	status: string;
	role: string;
	created_at: string;
	updated_at: string;
};

export type KnowledgeBase = {
	id: string;
	project_id: string;
	bot_id: string;
	chat_id: string | null;
	name: string;
	created_at: string;
};

export type Source = {
	id: string;
	project_id: string;
	knowledge_base_id: string;
	uploaded_by: string;
	display_name: string;
	version_id: string;
	job_id: string | null;
	version: number;
	filename: string;
	content_type: string;
	byte_size: number;
	status:
		| 'uploaded'
		| 'queued'
		| 'processing'
		| 'ready'
		| 'failed'
		| string;
	created_at: string;
};

export type SourceInspection = {
	source_id: string;
	version: number;
	filename: string;
	status: string;
	url: string;
};

export type Citation = {
	source_id: string;
	chunk_id: string;
	source_filename: string;
	excerpt: string;
	page_number: number | null;
	element_ids: string[];
};

export type ToolCall = {
	id: string;
	type: string;
	label: string;
	status: 'running' | 'completed' | 'failed';
	input?: unknown;
	output?: unknown;
};

export type Message = {
	id: string;
	chat_id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	citations: Citation[];
	tool_calls?: ToolCall[];
	reasoning?: string;
	created_at: string;
};
