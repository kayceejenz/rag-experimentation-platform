import psycopg
from modules.jobs.models.job_model import (
    IngestionJob,
    IngestionJobDetails,
    JobStatus,
    PipelineStage,
)
from psycopg.rows import dict_row


class JobRepository:
    def __init__(self, database_url: str, lease_seconds: int = 300) -> None:
        self.database_url = database_url
        self.lease_seconds = lease_seconds

    def claim_next(self, worker_id: str) -> IngestionJob | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "with candidate as (select id from ragapp.ingestion_jobs "
                "where attempts<max_attempts and ((status='queued' and available_at<=now()) or "
                "(status='running' and lease_expires_at<now())) "
                "and (stage='chunk' or specification_id is null or exists("
                "select 1 from ragapp.ingestion_jobs dependency where dependency.source_version_id="
                "ingestion_jobs.source_version_id and dependency.stage='chunk' and "
                "dependency.specification_id=ingestion_jobs.specification_id and dependency.status='completed')) "
                "order by priority,created_at for update skip locked limit 1) "
                "update ragapp.ingestion_jobs j set status='running',attempts=attempts+1,"
                "locked_at=now(),locked_by=%s,lease_expires_at=now()+(%s*interval '1 second') "
                "from candidate c,ragapp.source_versions sv,ragapp.sources s "
                "where j.id=c.id and sv.id=j.source_version_id and s.id=sv.source_id "
                "returning j.*,sv.source_id,sv.storage_key,sv.content_type,"
                "sv.byte_size,sv.content_sha256,s.project_id,s.knowledge_base_id,s.uploaded_by",
                (worker_id, self.lease_seconds),
            ).fetchone()
            if row:
                db.execute(
                    "update ragapp.source_versions set status='processing',"
                    "processing_started_at=coalesce(processing_started_at,now()),"
                    "error_code=null,error_message=null where id=%s",
                    (row["source_version_id"],),
                )
        return self._model(row) if row else None

    def get_for_user(self, job_id, user_id) -> IngestionJobDetails | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select j.*,sv.source_id,sv.filename,sv.status source_status,"
                "sv.element_count,sv.chunk_count,sv.processing_started_at,"
                "sv.processing_completed_at,s.project_id,s.knowledge_base_id "
                "from ragapp.ingestion_jobs j "
                "join ragapp.source_versions sv on sv.id=j.source_version_id "
                "join ragapp.sources s on s.id=sv.source_id "
                "join ragapp.project_members pm on pm.project_id=s.project_id "
                "where j.id=%s and pm.user_id=%s and s.deleted_at is null",
                (job_id, user_id),
            ).fetchone()
        if not row:
            return None
        return IngestionJobDetails(
            id=row["id"],
            source_version_id=row["source_version_id"],
            source_id=row["source_id"],
            project_id=row["project_id"],
            knowledge_base_id=row["knowledge_base_id"],
            filename=row["filename"],
            status=JobStatus(row["status"]),
            source_status=row["source_status"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            element_count=row["element_count"],
            chunk_count=row["chunk_count"],
            last_error=row["last_error"],
            available_at=row["available_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            processing_started_at=row["processing_started_at"],
            processing_completed_at=row["processing_completed_at"],
            completed_at=row["completed_at"],
        )

    def complete(self, job: IngestionJob, element_count: int, chunk_count: int) -> None:
        with psycopg.connect(self.database_url) as db:
            db.execute(
                "update ragapp.ingestion_jobs set status='completed',completed_at=now(),"
                "lease_expires_at=null where id=%s",
                (job.id,),
            )
            db.execute(
                "update ragapp.source_versions set status='ready',element_count=%s,chunk_count=%s,"
                "processing_completed_at=now(),parser_name='unstructured-api' where id=%s",
                (element_count, chunk_count, job.source_version_id),
            )

    def fail(self, job: IngestionJob, error: str, permanent: bool = False) -> None:
        terminal = permanent or job.attempts >= job.max_attempts
        with psycopg.connect(self.database_url) as db:
            db.execute(
                "update ragapp.ingestion_jobs set status=%s,last_error=%s,locked_at=null,"
                "locked_by=null,lease_expires_at=null,"
                "available_at=now()+(least(attempts,6)*interval '30 seconds'),"
                "completed_at=case when %s then now() else null end where id=%s",
                ("failed" if terminal else "queued", error[:4000], terminal, job.id),
            )
            db.execute(
                "update ragapp.source_versions set status=%s,error_code='ingestion_failed',"
                "error_message=%s,"
                "processing_completed_at=case when %s then now() else null end where id=%s",
                (
                    "failed" if terminal else "queued",
                    error[:4000],
                    terminal,
                    job.source_version_id,
                ),
            )

    def renew_lease(self, job_id) -> None:
        with psycopg.connect(self.database_url) as db:
            db.execute(
                "update ragapp.ingestion_jobs "
                "set lease_expires_at=now()+(%s*interval '1 second') "
                "where id=%s and status='running'",
                (self.lease_seconds, job_id),
            )

    @staticmethod
    def _model(row) -> IngestionJob:
        return IngestionJob(
            id=row["id"],
            source_version_id=row["source_version_id"],
            source_id=row["source_id"],
            project_id=row["project_id"],
            knowledge_base_id=row["knowledge_base_id"],
            storage_key=row["storage_key"],
            uploaded_by=row["uploaded_by"],
            content_type=row["content_type"],
            byte_size=row["byte_size"],
            content_sha256=row["content_sha256"],
            stage=PipelineStage(row["stage"]),
            specification_id=row["specification_id"],
            status=JobStatus(row["status"]),
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            available_at=row["available_at"],
        )
