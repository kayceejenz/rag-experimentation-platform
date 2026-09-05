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
	| 'prompts'
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

export type PromptVersion = {
	id: string;
	prompt_id: string;
	project_id: string;
	version: number;
	template: string;
	variables: string[];
	content_sha256: string;
	change_note: string | null;
	created_by: string | null;
	created_at: string;
};
export type PromptAsset = {
	id: string;
	project_id: string;
	name: string;
	purpose: string | null;
	description: string | null;
	prompt_type: 'system' | 'rag_answer' | 'evaluation';
	origin: 'preinstalled' | 'custom';
	preset_key: string | null;
	status: 'active' | 'archived';
	created_by: string | null;
	created_at: string;
	updated_at: string;
	latest_version_id: string;
	latest_version: number;
	variables: string[];
	content_sha256: string;
};

export type BenchmarkCase = {
	case_id: string;
	question: string;
	reference_answer: string | null;
	expected_context: string | null;
	tags: string[];
};

export type BenchmarkDataset = {
	id: string;
	project_id: string;
	name: string;
	description: string | null;
	version: number;
	content?: BenchmarkCase[];
	example_count: number;
	version_count: number;
	content_sha256: string;
	created_by: string | null;
	created_at: string;
};

export type BenchmarkVersion = {
	id: string;
	version: number;
	description: string | null;
	example_count: number;
	content_sha256: string;
	created_by: string | null;
	created_at: string;
};
export type Experiment = {
	id: string;
	project_id: string;
	name: string;
	description: string | null;
	hypothesis: string;
	benchmark_dataset_id: string;
	benchmark_name: string;
	benchmark_version: number;
	benchmark_cases: number;
	metrics: string[];
	primary_metric: string;
	status: 'draft' | 'ready' | 'completed' | 'archived';
	variant_count: number;
	created_at: string;
	updated_at: string;
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
	active_revision_version: number | null;
	source_run_id: string | null;
	source_variant_run_id: string | null;
	source_experiment_name: string | null;
	source_variant_name: string | null;
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
	event_type:
		| 'knowledge.document_uploaded'
		| 'knowledge.document_deleted'
		| 'knowledge.folder_created'
		| string;
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
