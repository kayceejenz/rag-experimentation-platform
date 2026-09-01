export type Project = {
	id: string;
	workspace_id: string;
	owner_id: string;
	name: string;
	description: string | null;
	role: string;
	is_default: boolean;
	created_at: string;
	updated_at: string;
	permissions: Record<ProjectFeature, FeaturePermission>;
};

export type ProjectFeature =
	| 'knowledge'
	| 'indexes'
	| 'experiments'
	| 'benchmarks'
	| 'assistants'
	| 'runs'
	| 'settings';

export type FeaturePermission = { view: boolean; manage: boolean };

export type ProjectMember = {
	user_id: string;
	email: string;
	display_name: string | null;
	role: 'owner' | 'editor' | 'viewer';
	joined_at: string;
	permissions: Record<ProjectFeature, FeaturePermission>;
};

export type Assistant = {
	id: string;
	project_id: string;
	created_by: string;
	name: string;
	description: string | null;
	status: 'active' | 'archived';
	role: string;
	created_at: string;
	updated_at: string;
};

export type Chat = {
	id: string;
	assistant_id: string;
	project_id: string;
	created_by: string;
	title: string;
	status: string;
	role: string;
	created_at: string;
	updated_at: string;
};

export type KnowledgeBase = {
	id: string;
	project_id: string;
	created_by: string;
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
	folder_id: string | null;
};

export type KnowledgeFolder = {
	id: string;
	knowledge_base_id: string;
	parent_id: string | null;
	name: string;
	created_at: string;
};

export type SourceInspection = {
	source_id: string;
	version: number;
	filename: string;
	status: string;
	url: string;
};

export type KnowledgeActivityEvent = {
	id: number;
	event_type: 'knowledge.document_uploaded' | 'knowledge.document_deleted' | 'knowledge.folder_created' | string;
	entity_id: string | null;
	actor_user_id: string | null;
	payload: {
		filename?: string;
		version?: number;
		byte_size?: number;
		content_type?: string;
		name?: string;
		parent_id?: string | null;
	};
	occurred_at: string;
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
	conversation_id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	citations: Citation[];
	tool_calls?: ToolCall[];
	reasoning?: string;
	created_at: string;
};
