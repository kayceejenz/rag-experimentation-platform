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
	chat_id: string;
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
	version_id: string;
	version: number;
	filename: string;
	status: string;
	parser_name: string | null;
	parser_version: string | null;
	parser_config: Record<string, unknown>;
	element_count: number;
	chunk_count: number;
	processing_started_at: string | null;
	processing_completed_at: string | null;
	error_code: string | null;
	error_message: string | null;
	elements: Array<{
		element_id: string;
		parent_element_id: string | null;
		category: string;
		content: string;
		page_number: number | null;
		coordinates: unknown;
		table_html: string | null;
		metadata: Record<string, unknown>;
		sequence_number: number;
	}>;
	chunks: Array<{
		id: string;
		position: number;
		content: string;
		token_count: number | null;
		page_from: number | null;
		page_to: number | null;
		metadata: Record<string, unknown>;
		element_ids: string[];
	}>;
};

export type Citation = {
	source_id: string;
	chunk_id: string;
	source_filename: string;
	excerpt: string;
	page_number: number | null;
	element_ids: string[];
};

export type Message = {
	id: string;
	chat_id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	citations: Citation[];
	created_at: string;
};
