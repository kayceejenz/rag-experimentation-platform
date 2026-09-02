import psycopg
from modules.sources.models.source_model import Source, SourceStatus
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class SourceRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def create(self, source: Source, content_sha256: str) -> Source:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            exists = db.execute(
                "select exists(select 1 from ragapp.sources where id=%s)",
                (source.id,),
            ).fetchone()["exists"]
            if not exists:
                db.execute(
                    "insert into ragapp.sources(id,project_id,knowledge_base_id,uploaded_by,"
                    "display_name,folder_id) values(%s,%s,%s,%s,%s,%s)",
                    (
                        source.id,
                        source.project_id,
                        source.knowledge_base_id,
                        source.uploaded_by,
                        source.display_name,
                        source.folder_id,
                    ),
                )
            row = db.execute(
                "insert into ragapp.source_versions(id,source_id,version,filename,content_type,"
                "byte_size,content_sha256,storage_key,status) "
                "values(%s,%s,%s,%s,%s,%s,%s,%s,'uploaded') "
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
            db.execute(
                "insert into ragapp.audit_events(project_id,knowledge_base_id,actor_user_id,"
                "event_type,entity_type,entity_id,payload) values(%s,%s,%s,%s,'source',%s,%s)",
                (
                    source.project_id,
                    source.knowledge_base_id,
                    source.uploaded_by,
                    "knowledge.document_uploaded",
                    source.id,
                    Jsonb(
                        {
                            "filename": source.display_name,
                            "version": source.version,
                            "byte_size": source.byte_size,
                            "content_type": source.content_type,
                        }
                    ),
                ),
            )
        return Source(
            **{
                **source.__dict__,
                "job_id": None,
                "status": SourceStatus.UPLOADED,
                "created_at": row["created_at"],
            }
        )

    def enqueue_stage(self, knowledge_base_id, user_id, stage: str) -> int:
        if not self.has_write_access(knowledge_base_id, user_id):
            return -1
        with psycopg.connect(self.database_url) as db:
            if stage == "chunk":
                rows = db.execute(
                    "select sv.id from ragapp.sources s join lateral "
                    "(select * from ragapp.source_versions where source_id=s.id order by version desc limit 1) sv on true "
                    "where s.knowledge_base_id=%s and s.deleted_at is null "
                    "and not exists(select 1 from ragapp.ingestion_jobs j where j.source_version_id=sv.id "
                    "and j.stage='chunk' and j.status in ('queued','running','completed'))",
                    (knowledge_base_id,),
                ).fetchall()
            else:
                rows = db.execute(
                    "select distinct sv.id from ragapp.sources s join lateral "
                    "(select * from ragapp.source_versions where source_id=s.id order by version desc limit 1) sv on true "
                    "join ragapp.chunks c on c.source_version_id=sv.id "
                    "where s.knowledge_base_id=%s and s.deleted_at is null "
                    "and not exists(select 1 from ragapp.ingestion_jobs j where j.source_version_id=sv.id "
                    "and j.stage='index' and j.status in ('queued','running','completed'))",
                    (knowledge_base_id,),
                ).fetchall()
            for (version_id,) in rows:
                db.execute(
                    "insert into ragapp.ingestion_jobs(source_version_id,stage) values(%s,%s)",
                    (version_id, stage),
                )
                db.execute(
                    "update ragapp.source_versions set status='queued',error_code=null,error_message=null where id=%s",
                    (version_id,),
                )
        return len(rows)

    def version_target(self, knowledge_base_id, filename, folder_id=None):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select s.id,coalesce(max(sv.version),0)+1 next_version "
                "from ragapp.sources s join ragapp.source_versions sv on sv.source_id=s.id "
                "where s.knowledge_base_id=%s and lower(s.display_name)=lower(%s) "
                "and s.folder_id is not distinct from %s and s.deleted_at is null "
                "group by s.id order by max(sv.version) desc limit 1",
                (knowledge_base_id, filename, folder_id),
            ).fetchone()

    def folder_exists(self, knowledge_base_id, folder_id):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.knowledge_folders where id=%s and knowledge_base_id=%s)",
                (folder_id, knowledge_base_id),
            ).fetchone()[0]

    def list_folders(self, knowledge_base_id, user_id):
        if not self.has_read_access(knowledge_base_id, user_id):
            return None
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select id,knowledge_base_id,parent_id,name,created_at from ragapp.knowledge_folders "
                "where knowledge_base_id=%s order by lower(name),id",
                (knowledge_base_id,),
            ).fetchall()

    def create_folder(self, knowledge_base_id, user_id, name, parent_id):
        if not self.has_write_access(knowledge_base_id, user_id):
            return None
        if parent_id and not self.folder_exists(knowledge_base_id, parent_id):
            return None
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            folder = db.execute(
                "insert into ragapp.knowledge_folders(knowledge_base_id,parent_id,name,created_by) "
                "values(%s,%s,%s,%s) returning id,knowledge_base_id,parent_id,name,created_at",
                (knowledge_base_id, parent_id, name, user_id),
            ).fetchone()
            project = db.execute(
                "select project_id from ragapp.knowledge_bases where id=%s",
                (knowledge_base_id,),
            ).fetchone()
            db.execute(
                "insert into ragapp.audit_events(project_id,knowledge_base_id,actor_user_id,event_type,"
                "entity_type,entity_id,payload) values(%s,%s,%s,'knowledge.folder_created','folder',%s,%s)",
                (
                    project["project_id"],
                    knowledge_base_id,
                    user_id,
                    folder["id"],
                    Jsonb(
                        {
                            "name": name,
                            "parent_id": str(parent_id) if parent_id else None,
                        }
                    ),
                ),
            )
        return folder

    def has_write_access(self, knowledge_base_id, user_id) -> bool:
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.knowledge_bases kb where kb.id=%s "
                "and ragapp.has_project_permission(kb.project_id,%s,'knowledge','manage') "
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
                "select exists(select 1 from ragapp.knowledge_bases kb where kb.id=%s "
                "and ragapp.has_project_permission(kb.project_id,%s,'knowledge','view') "
                "and kb.deleted_at is null)",
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

    def list_activity(self, knowledge_base_id, user_id, limit=100):
        if not self.has_read_access(knowledge_base_id, user_id):
            return None
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select id,event_type,entity_id,actor_user_id,payload,occurred_at "
                "from ragapp.audit_events where knowledge_base_id=%s "
                "order by occurred_at desc,id desc limit %s",
                (knowledge_base_id, limit),
            ).fetchall()

    def latest_version(self, knowledge_base_id, source_id, user_id):
        if not self.has_read_access(knowledge_base_id, user_id):
            return None
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select sv.* from ragapp.sources s join lateral "
                "(select candidate.* from ragapp.source_versions candidate "
                "where candidate.source_id=s.id order by "
                "(candidate.status='ready' and candidate.chunk_count>0) desc,"
                "candidate.version desc limit 1) sv on true "
                "where s.id=%s and s.knowledge_base_id=%s and s.deleted_at is null",
                (source_id, knowledge_base_id),
            ).fetchone()

    def delete(self, knowledge_base_id, source_id, user_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            allowed = db.execute(
                "select exists(select 1 from ragapp.sources s "
                "where s.id=%s and s.knowledge_base_id=%s "
                "and ragapp.has_project_permission(s.project_id,%s,'knowledge','manage') "
                "and s.deleted_at is null)",
                (source_id, knowledge_base_id, user_id),
            ).fetchone()["exists"]
            if not allowed:
                return None
            source = db.execute(
                "select s.project_id,s.display_name,sv.version,sv.byte_size,sv.content_type "
                "from ragapp.sources s join lateral (select * from ragapp.source_versions "
                "where source_id=s.id order by version desc limit 1) sv on true where s.id=%s",
                (source_id,),
            ).fetchone()
            rows = db.execute(
                "select storage_key from ragapp.source_versions where source_id=%s "
                "union select se.visual_storage_key from ragapp.source_elements se "
                "join ragapp.source_versions sv on sv.id=se.source_version_id "
                "where sv.source_id=%s and se.visual_storage_key is not null",
                (source_id, source_id),
            ).fetchall()
            db.execute(
                "insert into ragapp.audit_events(project_id,knowledge_base_id,actor_user_id,"
                "event_type,entity_type,entity_id,payload) values(%s,%s,%s,"
                "'knowledge.document_deleted','source',%s,%s)",
                (
                    source["project_id"],
                    knowledge_base_id,
                    user_id,
                    source_id,
                    Jsonb(
                        {
                            "filename": source["display_name"],
                            "version": source["version"],
                            "byte_size": source["byte_size"],
                            "content_type": source["content_type"],
                        }
                    ),
                ),
            )
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
            folder_id=row["folder_id"],
        )
