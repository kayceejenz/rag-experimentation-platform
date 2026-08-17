import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from modules.sources.models.error_model import SourceNotFoundError, SourcePermissionError
from modules.sources.models.source_model import (
    Source,
)
from integrations.storage import delete_file, upload_file


class SourceService:
    def __init__(self, repository, storage_dir: str) -> None:
        self.repository = repository
        self.storage_dir = storage_dir

    def upload(self, knowledge_base_id: UUID, user_id: UUID, file) -> Source:
        if not self.repository.has_write_access(knowledge_base_id, user_id):
            raise SourcePermissionError
        project_id = self.repository.project_id(knowledge_base_id)
        if not project_id:
            raise SourceNotFoundError

        source_id, version_id = uuid4(), uuid4()
        suffix = Path(file.filename or "document.bin").suffix.lower()
        storage_key = f"{project_id}/{source_id}/{version_id}{suffix}"
        digest = hashlib.sha256()
        byte_size = 0
        file.file.seek(0)
        while chunk := file.file.read(1024 * 1024):
            digest.update(chunk)
            byte_size += len(chunk)
        file.file.seek(0)


        stored_key = upload_file(
            storage_key,
            file.file,
            file.content_type or "application/octet-stream",
            self.storage_dir,
        )
        source = Source(
            id=source_id,
            project_id=project_id,
            knowledge_base_id=knowledge_base_id,
            uploaded_by=user_id,
            display_name=file.filename or "document",
            version_id=version_id,
            version=1,
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            storage_key=stored_key,
            byte_size=byte_size,
        )
        try:
            return self.repository.create_with_job(source, digest.hexdigest())
        except Exception:
            delete_file(stored_key, self.storage_dir)
            raise

    def list(self, knowledge_base_id: UUID, user_id: UUID) -> list[Source]:
        if not self.repository.has_read_access(knowledge_base_id, user_id):
            raise SourceNotFoundError
        return self.repository.list_for_user(knowledge_base_id, user_id)
