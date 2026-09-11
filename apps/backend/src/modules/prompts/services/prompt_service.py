import hashlib
import re
from typing import ClassVar

import psycopg.errors


class PromptService:
    TYPES: ClassVar[set[str]] = {"system", "rag_answer", "evaluation"}
    VARIABLE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")

    def __init__(self, repository):
        self.repository = repository

    def list(self, project_id, user_id):
        if not self.repository.can_access(project_id, user_id):
            raise PermissionError
        return self.repository.list(project_id)

    def create(
        self,
        project_id,
        user_id,
        name,
        purpose,
        description,
        prompt_type,
        template,
        change_note,
    ):
        self._manage(project_id, user_id)
        variables, digest = self._validate(prompt_type, template)
        try:
            return self.repository.create(
                project_id,
                user_id,
                name.strip(),
                self._optional(purpose),
                self._optional(description),
                prompt_type,
                template.strip(),
                variables,
                digest,
                self._optional(change_note),
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError("An active prompt with this name already exists") from None

    def detail(self, project_id, user_id, prompt_id):
        if not self.repository.can_access(project_id, user_id):
            raise PermissionError
        result = self.repository.detail(project_id, prompt_id)
        if not result:
            raise LookupError
        return result

    def add_version(self, project_id, user_id, prompt_id, template, change_note):
        self._manage(project_id, user_id)
        detail = self.repository.detail(project_id, prompt_id)
        if not detail:
            raise LookupError
        variables, digest = self._validate(detail["prompt"]["prompt_type"], template)
        try:
            row = self.repository.add_version(
                project_id,
                prompt_id,
                user_id,
                template.strip(),
                variables,
                digest,
                self._optional(change_note),
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError(
                "This template is identical to an existing version"
            ) from None
        if not row:
            raise LookupError
        return row

    def archive(self, project_id, user_id, prompt_id):
        self._manage(project_id, user_id)
        if not self.repository.archive(project_id, prompt_id):
            raise LookupError

    def _manage(self, p, u):
        if not self.repository.can_access(p, u, "manage"):
            raise PermissionError

    def _validate(self, prompt_type, template):
        if prompt_type not in self.TYPES:
            raise ValueError("Unsupported prompt type")
        value = template.strip()
        if not value:
            raise ValueError("Prompt template cannot be empty")
        variables = sorted(set(self.VARIABLE.findall(value)))
        unresolved = re.findall(r"{{|}}", self.VARIABLE.sub("", value))
        if unresolved:
            raise ValueError("Prompt contains invalid variable syntax")
        if prompt_type == "rag_answer" and not {"context", "question"}.issubset(
            variables
        ):
            raise ValueError("RAG answer prompts require {{context}} and {{question}}")
        return variables, hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def _optional(value):
        return value.strip() if value and value.strip() else None
