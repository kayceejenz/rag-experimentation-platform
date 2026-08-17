import psycopg
from psycopg.rows import dict_row

from modules.sources.models.source_model import Source, SourceStatus


class SourceRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def create_with_job(self, source: Source, content_sha256: str) -> Source:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            db.execute(
                "insert into ragapp.sources(id,project_id,knowledge_base_id,uploaded_by,"
                "display_name) "
                "values(%s,%s,%s,%s,%s)",
                (
                    source.id,
                    source.project_id,
                    source.knowledge_base_id,
                    source.uploaded_by,
                    source.display_name,
                ),
            )
            row = db.execute(
                "insert into ragapp.source_versions(id,source_id,version,filename,content_type,"
                "byte_size,content_sha256,storage_key,status) "
                "values(%s,%s,%s,%s,%s,%s,%s,%s,'queued') "
                "returning created_at",
                (
                    source.version_id,
                    source.id,
                    source.version,
                    source.filename,
                    source.content_type,
                    source.byte_size,
                    content_sha256,
                    source.storage_key,
                ),
            ).fetchone()
            job = db.execute(
                "insert into ragapp.ingestion_jobs(source_version_id) values(%s) returning id",
                (source.version_id,),
            ).fetchone()
        return Source(
            **{
                **source.__dict__,
                "job_id": job["id"],
                "status": SourceStatus.QUEUED,
                "created_at": row["created_at"],
            }
        )

    def has_write_access(self, knowledge_base_id, user_id) -> bool:
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.knowledge_bases kb "
                "join ragapp.project_members pm on pm.project_id=kb.project_id "
                "where kb.id=%s and pm.user_id=%s and pm.role in ('owner','editor') "
                "and kb.deleted_at is null)",
                (knowledge_base_id, user_id),
            ).fetchone()[0]

    def project_id(self, knowledge_base_id):
        with psycopg.connect(self.database_url) as db:
            row = db.execute(
                "select project_id from ragapp.knowledge_bases where id=%s and deleted_at is null",
                (knowledge_base_id,),
            ).fetchone()
        return row[0] if row else None

    def has_read_access(self, knowledge_base_id, user_id) -> bool:
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.knowledge_bases kb "
                "join ragapp.project_members pm on pm.project_id=kb.project_id "
                "where kb.id=%s and pm.user_id=%s and kb.deleted_at is null)",
                (knowledge_base_id, user_id),
            ).fetchone()[0]

    def list_for_user(self, knowledge_base_id, user_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            rows = db.execute(
                "select s.*,sv.id version_id,sv.version,sv.filename,sv.content_type,sv.storage_key,"
                "sv.byte_size,sv.status,ij.id job_id from ragapp.sources s "
                "join lateral (select * from ragapp.source_versions where source_id=s.id "
                "order by version desc limit 1) sv on true "
                "left join lateral (select id from ragapp.ingestion_jobs "
                "where source_version_id=sv.id order by created_at desc limit 1) ij on true "
                "join ragapp.project_members pm on pm.project_id=s.project_id "
                "where s.knowledge_base_id=%s and pm.user_id=%s and s.deleted_at is null "
                "order by s.created_at desc",
                (knowledge_base_id, user_id),
            ).fetchall()
        return [self._model(row) for row in rows]

    @staticmethod
    def _model(row) -> Source:
        return Source(
            id=row["id"],
            project_id=row["project_id"],
            knowledge_base_id=row["knowledge_base_id"],
            uploaded_by=row["uploaded_by"],
            display_name=row["display_name"],
            version_id=row["version_id"],
            job_id=row["job_id"],
            version=row["version"],
            filename=row["filename"],
            content_type=row["content_type"],
            storage_key=row["storage_key"],
            byte_size=row["byte_size"],
            status=SourceStatus(row["status"]),
            created_at=row["created_at"],
        )
