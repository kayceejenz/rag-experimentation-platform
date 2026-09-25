export type EmbeddingModel = {
	id: string;
	provider: string;
	model_name: string;
	dimensions: number;
	distance_metric: string;
	configuration: Record<string, unknown>;
};

export type Strategy = { id: string; name: string; provider: string };

export type IndexBuild = {
	id: string;
	configuration: {
		name: string;
		chunking: { strategy: string };
		knowledge?: { scope: 'root' | 'folders'; folder_ids: string[] };
		embedding: {
			provider: string;
			model: string;
			dimensions: number;
		};
	};
	configuration_hash: string;
	created_at: string;
	job_count: number;
	completed_jobs: number;
	failed_jobs: number;
	active_jobs: number;
};

export type IndexCatalog = {
	embedding_models: EmbeddingModel[];
	chunking_strategies: Strategy[];
	indexes: IndexBuild[];
};

export type Artifact = {
	id: string;
	kind: string;
	role: string;
	storage_type: string;
	storage_key: string | null;
	manifest: Record<string, unknown> | null;
};

export type IndexTrace = {
	id: string;
	kind: string;
	status: string;
	worker_id: string | null;
	attempt: number;
	parameters: Record<string, unknown>;
	created_at: string;
	started_at: string | null;
	completed_at: string | null;
	error_message: string | null;
	inputs: Artifact[];
	outputs: Artifact[];
};

export type IndexDetail = {
	specification: IndexBuild;
	jobs: Array<{
		id: string;
		stage: string;
		status: string;
		display_name: string;
		version: number;
		source_version_id: string;
		created_at: string;
	}>;
	traces: IndexTrace[];
};

export type ArtifactPreview = {
	artifact: Artifact;
	records: Array<Record<string, unknown>>;
	limit: number;
};
