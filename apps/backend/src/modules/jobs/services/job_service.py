from uuid import UUID

from modules.jobs.models.error_model import JobNotFoundError
from modules.jobs.models.job_model import IngestionJobDetails


class JobService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def get(self, job_id: UUID, user_id: UUID) -> IngestionJobDetails:
        job = self.repository.get_for_user(job_id, user_id)
        if not job:
            raise JobNotFoundError
        return job
