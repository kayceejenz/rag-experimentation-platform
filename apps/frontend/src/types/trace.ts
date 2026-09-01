export type ExecutionStatus =
	| 'pending'
	| 'running'
	| 'completed'
	| 'failed'
	| 'cancelled';

export type Execution = {
	id: string;
	project_id: string;
	knowledge_base_id?: string | null;
	kind: string;
	specification_id: string | null;
	status: ExecutionStatus;
	idempotency_key: string | null;
	code_revision: string;
	worker_id: string | null;
	attempt: number;
	parameters: Record<string, unknown>;
	result_summary: Record<string, unknown> | null;
	error_code: string | null;
	error_message: string | null;
	created_at: string;
	started_at: string | null;
	completed_at: string | null;
};

export type Specification = {
	id: string;
	kind: string;
	schema_version: number;
	configuration: Record<string, unknown>;
	configuration_hash: string;
	created_at: string;
};

export type Artifact = {
	id: string;
	kind: string;
	storage_type: string;
	storage_key: string | null;
	content_sha256: string | null;
	manifest: Record<string, unknown> | null;
	manifest_hash: string | null;
	media_type: string | null;
	byte_size: number | null;
	created_at: string;
};

export type ArtifactLink = {
	role: string;
	position: number;
	artifact: Artifact;
};

export type ExecutionLineage = {
	execution: Execution;
	specification: Specification | null;
	inputs: ArtifactLink[];
	outputs: ArtifactLink[];
};
