from typing import Protocol
from uuid import UUID

from modules.jobs.models.job_model import IngestionJob, IngestionJobDetails


class JobQueue(Protocol):
    def enqueue(self, job: IngestionJob) -> None: ...
    def claim_next(self, worker_id: str) -> IngestionJob | None: ...
    def complete(self, job: IngestionJob) -> None: ...
    def fail(self, job: IngestionJob, error: str, permanent: bool = False) -> None: ...


class JobReader(Protocol):
    def get_for_user(
        self, job_id: UUID, user_id: UUID
    ) -> IngestionJobDetails | None: ...
