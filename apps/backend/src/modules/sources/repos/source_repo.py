import psycopg
from psycopg.rows import dict_row

from modules.sources.models.source_model import Source, SourceStatus


class SourceRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def create_with_job(self, source: Source, content_sha256: str) -> Source:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            exists = db.execute(
                "select exists(select 1 from ragapp.sources where id=%s)",
                (source.id,),
            ).fetchone()["exists"]
            if not exists:
                db.execute(
                    "insert into ragapp.sources(id,project_id,knowledge_base_id,uploaded_by,"
                    "display_name) values(%s,%s,%s,%s,%s)",
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

    def version_target(self, knowledge_base_id, filename):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select s.id,coalesce(max(sv.version),0)+1 next_version "
                "from ragapp.sources s join ragapp.source_versions sv on sv.source_id=s.id "
                "where s.knowledge_base_id=%s and lower(s.display_name)=lower(%s) "
                "and s.deleted_at is null group by s.id order by max(sv.version) desc limit 1",
                (knowledge_base_id, filename),
            ).fetchone()

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

    def inspection(self, knowledge_base_id, source_id, user_id):
        if not self.has_read_access(knowledge_base_id, user_id):
            return None
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            version = db.execute(
                "select sv.* from ragapp.sources s join lateral "
                "(select candidate.* from ragapp.source_versions candidate "
                "where candidate.source_id=s.id order by "
                "(candidate.status='ready' and candidate.chunk_count>0) desc,"
                "candidate.version desc limit 1) sv on true "
                "where s.id=%s and s.knowledge_base_id=%s and s.deleted_at is null",
                (source_id, knowledge_base_id),
            ).fetchone()
            if not version:
                return None
            elements = db.execute(
                "select element_id,parent_element_id,category,content,page_number,"
                "coordinates,table_html,metadata,sequence_number "
                "from ragapp.source_elements where source_version_id=%s "
                "order by sequence_number",
                (version["id"],),
            ).fetchall()
            chunks = db.execute(
                "select c.id,c.position,c.content,c.token_count,c.page_from,c.page_to,"
                "c.metadata,coalesce(array_agg(se.element_id order by ce.element_order) "
                "filter (where se.element_id is not null),'{}') element_ids "
                "from ragapp.chunks c left join ragapp.chunk_elements ce on ce.chunk_id=c.id "
                "left join ragapp.source_elements se on se.id=ce.source_element_id "
                "where c.source_version_id=%s group by c.id order by c.position",
                (version["id"],),
            ).fetchall()
        return {"version": version, "elements": elements, "chunks": chunks}

    def delete(self, knowledge_base_id, source_id, user_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            allowed = db.execute(
                "select exists(select 1 from ragapp.sources s "
                "join ragapp.project_members pm on pm.project_id=s.project_id "
                "where s.id=%s and s.knowledge_base_id=%s and pm.user_id=%s "
                "and pm.role in ('owner','editor') and s.deleted_at is null)",
                (source_id, knowledge_base_id, user_id),
            ).fetchone()["exists"]
            if not allowed:
                return None
            rows = db.execute(
                "select storage_key from ragapp.source_versions where source_id=%s "
                "union select se.visual_storage_key from ragapp.source_elements se "
                "join ragapp.source_versions sv on sv.id=se.source_version_id "
                "where sv.source_id=%s and se.visual_storage_key is not null",
                (source_id, source_id),
            ).fetchall()
            db.execute("delete from ragapp.sources where id=%s", (source_id,))
        return [row["storage_key"] for row in rows]

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
