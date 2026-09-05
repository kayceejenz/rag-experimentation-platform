import hashlib
import json

import psycopg.errors


class ExperimentService:
    SUPPORTED_METRICS = {
        "context_precision",
        "context_recall",
        "faithfulness",
        "answer_relevance",
        "hallucination_detection",
        "retrieval_latency",
        "total_latency",
        "token_count",
        "estimated_cost",
    }
    JUDGE_METRICS = {
        "context_precision",
        "context_recall",
        "faithfulness",
        "answer_relevance",
        "hallucination_detection",
    }

    def __init__(self, repository, runs=None, code_revision="development", generation_models=None):
        self.repository = repository
        self.runs = runs
        self.code_revision = code_revision
        self.generation_models = tuple(model for model in (generation_models or []) if model)

    def catalog(self, project_id, user_id):
        self._authorise(project_id, user_id)
        catalog = self.repository.catalog(project_id)
        catalog["generation_models"] = list(self.generation_models)
        return catalog

    def create(
        self,
        project_id,
        user_id,
        name,
        description,
        hypothesis,
        dataset_id,
        metrics,
        primary_metric,
    ):
        self._authorise(project_id, user_id, "manage")
        cleaned_metrics = sorted(set(metrics))
        unsupported = set(cleaned_metrics) - self.SUPPORTED_METRICS
        if unsupported:
            raise ValueError(f"Unsupported metrics: {', '.join(sorted(unsupported))}")
        if not cleaned_metrics:
            raise ValueError("Select at least one evaluation metric")
        if primary_metric not in cleaned_metrics:
            raise ValueError("Primary metric must be one of the selected metrics")
        if not self.repository.dataset_exists(project_id, dataset_id):
            raise LookupError("Benchmark dataset not found")
        try:
            return self.repository.create_experiment(
                project_id,
                user_id,
                name.strip(),
                self._optional(description),
                hypothesis.strip(),
                dataset_id,
                cleaned_metrics,
                primary_metric,
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError(
                "An active experiment with this name already exists"
            ) from None

    def detail(self, project_id, user_id, experiment_id):
        self._authorise(project_id, user_id)
        result = self.repository.detail(project_id, experiment_id)
        if not result:
            raise LookupError("Experiment not found")
        if self.runs:
            result["runs"] = self.runs.runs(experiment_id)
        return result

    def project_runs(self, project_id, user_id, limit=100):
        self._authorise(project_id, user_id)
        return {"runs": self.runs.project_runs(project_id, limit)}

    def start_run(self, project_id, user_id, experiment_id, variant_ids):
        self._authorise(project_id, user_id, "manage")
        if not self.repository.detail(project_id, experiment_id):
            raise LookupError("Experiment not found")
        return self.runs.enqueue(
            project_id,
            experiment_id,
            user_id,
            self.code_revision,
            self.generation_models,
            variant_ids,
        )

    def run_detail(self, project_id, user_id, experiment_id, run_id):
        self._authorise(project_id, user_id)
        result = self.runs.run_detail(project_id, run_id)
        if not result or str(result["run"]["experiment_id"]) != str(experiment_id):
            raise LookupError("Experiment run not found")
        return result

    def delete_variant(self, project_id, user_id, experiment_id, variant_id):
        self._authorise(project_id, user_id, "manage")
        result = self.repository.delete_variant(project_id, experiment_id, variant_id)
        if result == "missing":
            raise LookupError("Experiment variant not found")
        if result == "used":
            raise RuntimeError(
                "This variant belongs to an experiment run and must be retained for lineage"
            )

    def add_variant(
        self,
        project_id,
        user_id,
        experiment_id,
        name,
        index_id,
        system_version_id,
        rag_version_id,
        retrieval,
        generation,
    ):
        self._authorise(project_id, user_id, "manage")
        model = generation.get("model")
        if self.generation_models and model not in self.generation_models:
            raise ValueError(
                f"Generation model '{model}' is not enabled for this deployment"
            )
        assets = self.repository.variant_assets(
            project_id, experiment_id, index_id, system_version_id, rag_version_id
        )
        experiment, index, system, rag, evaluator_rows = assets
        if not experiment:
            raise LookupError("Experiment not found")
        if not index:
            raise ValueError("Select an active index")
        if not system or not rag:
            raise ValueError("Select valid system and RAG answer prompt versions")
        available = {row["purpose"]: str(row["version_id"]) for row in evaluator_rows}
        required = set(experiment["metrics"]) & self.JUDGE_METRICS
        missing = required - set(available)
        if missing:
            raise ValueError(
                f"Missing evaluation prompts for: {', '.join(sorted(missing))}"
            )
        evaluators = {metric: available[metric] for metric in sorted(required)}
        configuration = {
            "index_specification_id": str(index_id),
            "system_prompt_version_id": str(system_version_id),
            "rag_prompt_version_id": str(rag_version_id),
            "evaluator_prompt_versions": evaluators,
            "retrieval": retrieval,
            "generation": generation,
        }
        canonical = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        try:
            return self.repository.create_variant(
                project_id,
                experiment_id,
                user_id,
                name.strip(),
                index_id,
                system_version_id,
                rag_version_id,
                evaluators,
                retrieval,
                generation,
                digest,
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError("Variant name or configuration already exists") from None

    def _authorise(self, project_id, user_id, action="view"):
        if not self.repository.can_access(project_id, user_id, action):
            raise PermissionError

    @staticmethod
    def _optional(value):
        return value.strip() if value and value.strip() else None
