from modules.core.models.specification_model import SpecificationKind


class IndexService:
    STRATEGIES = {"by_title", "basic"}

    def __init__(self, repository, specifications) -> None:
        self.repository = repository
        self.specifications = specifications

    def catalog(self, project_id, user_id):
        if not self.repository.can_access(project_id, user_id):
            raise PermissionError
        return self.repository.models(), self.repository.builds(project_id)

    def create(self, project_id, user_id, knowledge_base_id, name, model_id, strategy, folder_ids):
        if not self.repository.can_access(project_id, user_id, write=True):
            raise PermissionError
        if strategy not in self.STRATEGIES:
            raise ValueError("Unsupported chunking strategy")
        model = self.repository.model(model_id)
        if not model or not self.repository.knowledge_base_exists(project_id, knowledge_base_id):
            raise LookupError
        folder_ids = list(dict.fromkeys(folder_ids))
        if folder_ids and not self.repository.folders_exist(knowledge_base_id, folder_ids):
            raise ValueError("One or more selected folders do not belong to this Knowledge Base")
        specification = self.specifications.register(
            project_id,
            user_id,
            SpecificationKind.PIPELINE,
            1,
            {
                "name": name,
                "partitioning": {"provider": "unstructured", "strategy": "auto", "pdf_strategy": "hi_res", "ocr_languages": ["eng"]},
                "chunking": {"strategy": strategy},
                "embedding": {"provider": model["provider"], "model": model["model_name"], "dimensions": model["dimensions"]},
                "knowledge": {
                    "knowledge_base_id": str(knowledge_base_id),
                    "scope": "folders" if folder_ids else "root",
                    "folder_ids": [str(folder_id) for folder_id in folder_ids],
                },
            },
        )
        queued, documents = self.repository.enqueue(project_id, knowledge_base_id, specification.id, folder_ids)
        return specification, queued, documents

    def detail(self, project_id, user_id, specification_id):
        if not self.repository.can_access(project_id, user_id):
            raise PermissionError
        detail = self.repository.detail(project_id, specification_id)
        if detail is None:
            raise LookupError
        return detail

    def artifact_preview(self, project_id, user_id, specification_id, artifact_id):
        if not self.repository.can_access(project_id, user_id):
            raise PermissionError
        preview = self.repository.artifact_preview(project_id, specification_id, artifact_id)
        if preview is None:
            raise LookupError
        return preview

    def refresh(self, project_id, user_id, specification_id, knowledge_base_id):
        if not self.repository.can_access(project_id, user_id, write=True):
            raise PermissionError
        if not self.repository.specification_exists(project_id, specification_id):
            raise LookupError
        if not self.repository.knowledge_base_exists(project_id, knowledge_base_id):
            raise LookupError
        scope = self.repository.specification_scope(project_id, specification_id)
        if scope is None:
            raise LookupError
        configured_knowledge_base_id, folder_ids = scope
        if configured_knowledge_base_id != knowledge_base_id:
            raise ValueError("Index does not belong to this Knowledge Base")
        queued, sources = self.repository.enqueue(
            project_id, knowledge_base_id, specification_id, folder_ids
        )
        return {"queued_jobs": queued, "new_sources": sources}

    def delete(self, project_id, user_id, specification_id):
        if not self.repository.can_access(project_id, user_id, write=True):
            raise PermissionError
        if not self.repository.retire(project_id, specification_id, user_id):
            raise LookupError
