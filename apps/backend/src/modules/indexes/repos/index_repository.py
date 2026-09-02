from uuid import UUID

import psycopg
from psycopg.rows import dict_row


class IndexRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def can_access(self, project_id, user_id, write=False):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select ragapp.has_project_permission(%s,%s,'indexes',%s)",
                (project_id, user_id, "manage" if write else "view"),
            ).fetchone()[0]

    def models(self):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select id,provider,model_name,dimensions,distance_metric,configuration "
                "from ragapp.embedding_models where is_active order by provider,model_name,dimensions"
            ).fetchall()

    def model(self, model_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select * from ragapp.embedding_models where id=%s and is_active",
                (model_id,),
            ).fetchone()

    def knowledge_base_exists(self, project_id, knowledge_base_id):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.knowledge_bases where id=%s and project_id=%s and deleted_at is null)",
                (knowledge_base_id, project_id),
            ).fetchone()[0]

    def folders_exist(self, knowledge_base_id, folder_ids):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select count(*)=%s from ragapp.knowledge_folders "
                "where knowledge_base_id=%s and id=any(%s)",
                (len(folder_ids), knowledge_base_id, folder_ids),
            ).fetchone()[0]

    def enqueue(self, project_id, knowledge_base_id, specification_id, folder_ids=None):
        queued = 0
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            folder_filter = ""
            parameters = [project_id, knowledge_base_id]
            if folder_ids:
                folder_filter = (
                    "and s.folder_id in (with recursive selected_folders as ("
                    "select id from ragapp.knowledge_folders where knowledge_base_id=%s and id=any(%s) "
                    "union select child.id from ragapp.knowledge_folders child "
                    "join selected_folders parent on child.parent_id=parent.id) "
                    "select id from selected_folders) "
                )
                parameters.extend([knowledge_base_id, folder_ids])
            parameters.append(specification_id)
            versions = db.execute(
                "select sv.id from ragapp.sources s join lateral "
                "(select candidate.id from ragapp.source_versions candidate "
                "where candidate.source_id=s.id order by candidate.version desc limit 1) sv on true "
                "where s.project_id=%s and s.knowledge_base_id=%s and s.deleted_at is null "
                + folder_filter
                + "and not exists(select 1 from ragapp.ingestion_jobs existing "
                "where existing.source_version_id=sv.id and existing.specification_id=%s) "
                "order by s.id",
                parameters,
            ).fetchall()
            for version in versions:
                chunk = db.execute(
                    "insert into ragapp.ingestion_jobs(source_version_id,stage,priority,specification_id) "
                    "values(%s,'chunk',50,%s) on conflict do nothing returning id",
                    (version["id"], specification_id),
                ).fetchone()
                index = db.execute(
                    "insert into ragapp.ingestion_jobs(source_version_id,stage,priority,specification_id) "
                    "values(%s,'index',60,%s) on conflict do nothing returning id",
                    (version["id"], specification_id),
                ).fetchone()
                queued += int(chunk is not None) + int(index is not None)
                if chunk or index:
                    db.execute(
                        "update ragapp.source_versions set status='queued' where id=%s",
                        (version["id"],),
                    )
        return queued, len(versions)

    def specification_scope(self, project_id, specification_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select configuration from ragapp.specifications where id=%s and project_id=%s "
                "and kind='pipeline' and not exists(select 1 from ragapp.index_retirements r "
                "where r.specification_id=specifications.id)",
                (specification_id, project_id),
            ).fetchone()
        if not row:
            return None
        knowledge = row["configuration"].get("knowledge", {})
        knowledge_base_id = knowledge.get("knowledge_base_id")
        if not knowledge_base_id:
            return None
        return UUID(knowledge_base_id), [
            UUID(value) for value in knowledge.get("folder_ids", [])
        ]

    def specification_exists(self, project_id, specification_id):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.specifications "
                "where id=%s and project_id=%s and kind='pipeline' "
                "and not exists(select 1 from ragapp.index_retirements r "
                "where r.specification_id=specifications.id))",
                (specification_id, project_id),
            ).fetchone()[0]

    def builds(self, project_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select s.id,s.configuration,s.configuration_hash,s.created_at,"
                "count(j.id) job_count,count(j.id) filter(where j.status='completed') completed_jobs,"
                "count(j.id) filter(where j.status='failed') failed_jobs,"
                "count(j.id) filter(where j.status in('queued','running')) active_jobs "
                "from ragapp.specifications s left join ragapp.ingestion_jobs j on j.specification_id=s.id "
                "where s.project_id=%s and s.kind='pipeline' "
                "and not exists(select 1 from ragapp.index_retirements r where r.specification_id=s.id) "
                "group by s.id order by s.created_at desc",
                (project_id,),
            ).fetchall()

    def detail(self, project_id, specification_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            specification = db.execute(
                "select id,configuration,configuration_hash,created_at from ragapp.specifications "
                "where id=%s and project_id=%s and kind='pipeline' "
                "and not exists(select 1 from ragapp.index_retirements r "
                "where r.specification_id=specifications.id)",
                (specification_id, project_id),
            ).fetchone()
            if not specification:
                return None
            jobs = db.execute(
                "select j.id,j.stage,j.status,j.attempts,j.created_at,j.completed_at,"
                "s.id source_id,s.display_name,sv.id source_version_id,sv.version "
                "from ragapp.ingestion_jobs j join ragapp.source_versions sv on sv.id=j.source_version_id "
                "join ragapp.sources s on s.id=sv.source_id where j.specification_id=%s "
                "order by j.created_at,j.stage",
                (specification_id,),
            ).fetchall()
            executions = db.execute(
                "select id,kind,status,worker_id,attempt,parameters,result_summary,error_code,error_message,"
                "created_at,started_at,completed_at from ragapp.executions "
                "where project_id=%s and specification_id=%s order by created_at desc",
                (project_id, specification_id),
            ).fetchall()
            traces = []
            for execution in executions:
                inputs = db.execute(
                    "select a.id,a.kind,a.storage_type,a.storage_key,a.manifest,a.content_sha256,a.created_at,l.role,l.position "
                    "from ragapp.execution_inputs l join ragapp.artifacts a on a.id=l.artifact_id "
                    "where l.execution_id=%s order by l.position",
                    (execution["id"],),
                ).fetchall()
                outputs = db.execute(
                    "select a.id,a.kind,a.storage_type,a.storage_key,a.manifest,a.content_sha256,a.created_at,l.role,l.position "
                    "from ragapp.execution_outputs l join ragapp.artifacts a on a.id=l.artifact_id "
                    "where l.execution_id=%s order by l.position",
                    (execution["id"],),
                ).fetchall()
                traces.append({**execution, "inputs": inputs, "outputs": outputs})
        return {"specification": specification, "jobs": jobs, "traces": traces}

    def artifact_preview(self, project_id, specification_id, artifact_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            artifact = db.execute(
                "select distinct a.id,a.kind,a.storage_type,a.storage_key,a.manifest,a.content_sha256,a.created_at "
                "from ragapp.artifacts a join ragapp.execution_outputs eo on eo.artifact_id=a.id "
                "join ragapp.executions e on e.id=eo.execution_id "
                "where a.id=%s and a.project_id=%s and e.project_id=%s and e.specification_id=%s "
                "and not exists(select 1 from ragapp.index_retirements r where r.specification_id=e.specification_id)",
                (artifact_id, project_id, project_id, specification_id),
            ).fetchone()
            if not artifact:
                return None
            manifest = artifact["manifest"] or {}
            source_version_id = manifest.get("source_version_id")
            records = []
            if source_version_id and artifact["kind"] == "element_dataset":
                records = db.execute(
                    "select element_id,category,content,page_number,sequence_number,metadata "
                    "from ragapp.source_elements where source_version_id=%s "
                    "order by sequence_number limit 100",
                    (source_version_id,),
                ).fetchall()
            elif source_version_id and artifact["kind"] == "chunk_dataset":
                records = db.execute(
                    "select id,position,content,page_from,page_to,metadata "
                    "from ragapp.chunks where source_version_id=%s order by position limit 100",
                    (source_version_id,),
                ).fetchall()
            elif source_version_id and artifact["kind"] == "embedding_dataset":
                records = db.execute(
                    "select ce.chunk_id,em.provider,em.model_name,em.dimensions,ce.embedding::text embedding "
                    "from ragapp.chunk_embeddings ce join ragapp.chunks c on c.id=ce.chunk_id "
                    "join ragapp.embedding_models em on em.id=ce.embedding_model_id "
                    "where c.source_version_id=%s order by c.position limit 100",
                    (source_version_id,),
                ).fetchall()
        return {"artifact": artifact, "records": records, "limit": 100}

    def retire(self, project_id, specification_id, user_id):
        with psycopg.connect(self.database_url) as db:
            specification = db.execute(
                "select id from ragapp.specifications where id=%s and project_id=%s "
                "and kind='pipeline' and not exists(select 1 from ragapp.index_retirements r "
                "where r.specification_id=specifications.id) for update",
                (specification_id, project_id),
            ).fetchone()
            if not specification:
                return False
            db.execute(
                "insert into ragapp.index_retirements(specification_id,project_id,retired_by) "
                "values(%s,%s,%s)",
                (specification_id, project_id, user_id),
            )
            db.execute(
                "update ragapp.ingestion_jobs set status='cancelled',completed_at=now(),"
                "locked_at=null,locked_by=null,lease_expires_at=null "
                "where specification_id=%s and status='queued'",
                (specification_id,),
            )
        return True
