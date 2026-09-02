from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from integrations.storage import delete_file, resolve_file, upload_file
from modules.sources.models.error_model import (
    SourceNotFoundError,
    SourcePermissionError,
    SourceTooLargeError,
)
from modules.sources.models.source_model import (
    Source,
    SourceStatus,
)


class SourceService:
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self, repository, storage_dir: str) -> None:
        self.repository = repository
        self.storage_dir = storage_dir

    def upload(
        self,
        knowledge_base_id: UUID,
        user_id: UUID,
        file,
        folder_id: UUID | None = None,
    ) -> Source:
        if not self.repository.has_write_access(knowledge_base_id, user_id):
            raise SourcePermissionError
        project_id = self.repository.project_id(knowledge_base_id)
        if not project_id:
            raise SourceNotFoundError

        filename = file.filename or "document"
        if folder_id and not self.repository.folder_exists(
            knowledge_base_id, folder_id
        ):
            raise SourceNotFoundError
        target = self.repository.version_target(knowledge_base_id, filename, folder_id)
        source_id = target["id"] if target else uuid4()
        version = target["next_version"] if target else 1
        version_id = uuid4()
        suffix = Path(file.filename or "document.bin").suffix.lower()
        storage_key = f"{project_id}/{source_id}/{version_id}{suffix}"
        digest = hashlib.sha256()
        byte_size = 0
        file.file.seek(0)
        while chunk := file.file.read(1024 * 1024):
            digest.update(chunk)
            byte_size += len(chunk)
            if byte_size > self.MAX_FILE_SIZE:
                raise SourceTooLargeError
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
            display_name=filename,
            version_id=version_id,
            version=version,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            storage_key=stored_key,
            byte_size=byte_size,
            folder_id=folder_id,
        )
        try:
            return self.repository.create(source, digest.hexdigest())
        except Exception:
            delete_file(stored_key, self.storage_dir)
            raise

    def trigger(self, knowledge_base_id: UUID, user_id: UUID, stage: str) -> int:
        count = self.repository.enqueue_stage(knowledge_base_id, user_id, stage)
        if count < 0:
            raise SourcePermissionError
        return count

    def list(self, knowledge_base_id: UUID, user_id: UUID) -> list[Source]:
        if not self.repository.has_read_access(knowledge_base_id, user_id):
            raise SourceNotFoundError
        return self.repository.list_for_user(knowledge_base_id, user_id)

    def activity(self, knowledge_base_id: UUID, user_id: UUID) -> list[dict]:
        events = self.repository.list_activity(knowledge_base_id, user_id)
        if events is None:
            raise SourceNotFoundError
        return events

    def folders(self, knowledge_base_id: UUID, user_id: UUID) -> list[dict]:
        folders = self.repository.list_folders(knowledge_base_id, user_id)
        if folders is None:
            raise SourceNotFoundError
        return folders

    def create_folder(
        self, knowledge_base_id: UUID, user_id: UUID, name: str, parent_id: UUID | None
    ):
        folder = self.repository.create_folder(
            knowledge_base_id, user_id, name.strip(), parent_id
        )
        if folder is None:
            raise SourcePermissionError
        return folder

    def inspection(
        self, knowledge_base_id: UUID, source_id: UUID, user_id: UUID
    ) -> dict:
        version = self.repository.latest_version(knowledge_base_id, source_id, user_id)
        if not version:
            raise SourceNotFoundError
        return {
            "source_id": source_id,
            "version": version["version"],
            "filename": version["filename"],
            "status": SourceStatus(version["status"]),
            "url": f"/api/v1/knowledge-bases/{knowledge_base_id}/sources/{source_id}/file",
        }

    def load_file(self, knowledge_base_id: UUID, source_id: UUID, user_id: UUID):
        version = self.repository.latest_version(knowledge_base_id, source_id, user_id)
        if not version:
            raise SourceNotFoundError
        path, temporary = resolve_file(version["storage_key"], self.storage_dir)
        return (
            path,
            temporary,
            version["content_type"] or "application/octet-stream",
            version["filename"],
        )

    def delete(self, knowledge_base_id: UUID, source_id: UUID, user_id: UUID) -> None:
        storage_keys = self.repository.delete(knowledge_base_id, source_id, user_id)
        if storage_keys is None:
            raise SourceNotFoundError
        for storage_key in storage_keys:
            delete_file(storage_key, self.storage_dir)
