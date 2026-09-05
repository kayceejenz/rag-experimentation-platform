import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ExecutionKind(StrEnum):
    INGESTION = "ingestion"
    PARTITION = "partition"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEX_BUILD = "index_build"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    EVALUATION = "evaluation"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Execution:
    project_id: UUID
    kind: ExecutionKind
    code_revision: str
    specification_id: UUID | None = None
    knowledge_base_id: UUID | None = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    idempotency_key: str | None = None
    worker_id: str | None = None
    attempt: int = 1
    parameters: dict[str, Any] = field(default_factory=dict)
    result_summary: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.code_revision.strip():
            raise ValueError("code_revision cannot be blank")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("idempotency_key cannot be blank")
        if self.worker_id is not None and not self.worker_id.strip():
            raise ValueError("worker_id cannot be blank")
        if self.attempt < 1:
            raise ValueError("attempt must be positive")


@dataclass(frozen=True)
class ExecutionArtifact:
    project_id: UUID
    execution_id: UUID
    artifact_id: UUID
    role: str
    position: int = 0

    def __post_init__(self) -> None:
        if re.fullmatch(r"[a-z][a-z0-9_]{1,63}", self.role) is None:
            raise ValueError(
                "role must use lowercase letters, numbers, and underscores"
            )
        if self.position < 0:
            raise ValueError("position cannot be negative")
