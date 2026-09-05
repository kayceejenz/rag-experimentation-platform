import hashlib
import json

import psycopg.errors


class BenchmarkService:
    def __init__(self, repository):
        self.repository = repository

    def list(self, project_id, user_id):
        self._authorise(project_id, user_id)
        return self.repository.list(project_id)

    def create(self, project_id, user_id, name, description, cases):
        self._authorise(project_id, user_id, "manage")
        content, digest = self._prepare_cases(cases)
        try:
            return self.repository.create(
                project_id,
                user_id,
                name.strip(),
                self._optional(description),
                content,
                digest,
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError("A benchmark dataset with this name already exists") from None

    def detail(self, project_id, user_id, dataset_id):
        self._authorise(project_id, user_id)
        result = self.repository.detail(project_id, dataset_id)
        if not result:
            raise LookupError
        return result

    def add_version(self, project_id, user_id, dataset_id, description, cases):
        self._authorise(project_id, user_id, "manage")
        content, digest = self._prepare_cases(cases)
        try:
            row = self.repository.add_version(
                project_id,
                dataset_id,
                user_id,
                self._optional(description),
                content,
                digest,
            )
        except psycopg.errors.UniqueViolation:
            raise ValueError("This dataset version already exists") from None
        if not row:
            raise LookupError
        return row

    def _authorise(self, project_id, user_id, action="view"):
        if not self.repository.can_access(project_id, user_id, action):
            raise PermissionError

    @staticmethod
    def _prepare_cases(cases):
        if not cases:
            raise ValueError("A benchmark dataset requires at least one test case")
        case_ids = [str(case["case_id"]) for case in cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Test case identifiers must be unique")
        content = sorted(cases, key=lambda case: str(case["case_id"]))
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return content, hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _optional(value):
        return value.strip() if value and value.strip() else None
