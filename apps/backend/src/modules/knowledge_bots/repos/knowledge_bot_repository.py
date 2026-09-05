from modules.knowledge_bots.models.models import KnowledgeBot, KnowledgeBotStatus
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from integrations.database import async_db_connection


class KnowledgeBotRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self):
        return async_db_connection(self.database_url, row_factory=dict_row)

    @staticmethod
    def model(row: dict) -> KnowledgeBot:
        return KnowledgeBot(
            id=row["id"],
            project_id=row["project_id"],
            created_by=row["created_by"],
            name=row["name"],
            description=row["description"],
            status=KnowledgeBotStatus(row["status"]),
            settings=row["settings"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            active_revision_version=row.get("active_revision_version"),
            source_run_id=row.get("source_run_id"),
            source_variant_run_id=row.get("source_variant_run_id"),
            source_experiment_name=row.get("source_experiment_name"),
            source_variant_name=row.get("source_variant_name"),
        )

    @staticmethod
    def select():
        return (
            "select b.*,ar.version active_revision_version,evr.run_id source_run_id,"
            "ar.experiment_variant_run_id source_variant_run_id,e.name source_experiment_name,"
            "ev.name source_variant_name from ragapp.assistants b "
            "left join ragapp.assistant_revisions ar on ar.id=b.active_revision_id "
            "left join ragapp.experiment_variant_runs evr on evr.id=ar.experiment_variant_run_id "
            "left join ragapp.experiment_variants ev on ev.id=evr.variant_id "
            "left join ragapp.experiments e on e.id=ev.experiment_id "
        )

    async def create(self, project_id, created_by, name, description, experiment_variant_run_id) -> KnowledgeBot:
        async with self.connect() as db:
            async with db.transaction():
                cursor = await db.execute(
                    "select evr.id,evr.run_id,ev.index_specification_id,"
                    "ev.system_prompt_version_id,ev.rag_prompt_version_id,"
                    "ev.retrieval_configuration,ev.generation_configuration,ev.configuration_hash "
                    "from ragapp.experiment_variant_runs evr "
                    "join ragapp.experiment_variants ev on ev.id=evr.variant_id "
                    "where evr.id=%s and evr.project_id=%s and evr.status='completed'",
                    (experiment_variant_run_id, project_id),
                )
                source = await cursor.fetchone()
                if not source:
                    raise ValueError("Select a completed experiment variant run")
                cursor = await db.execute(
                    "insert into ragapp.assistants(project_id,created_by,name,description) "
                    "values(%s,%s,%s,%s) returning *",
                    (project_id, created_by, name, description),
                )
                assistant = await cursor.fetchone()
                configuration = {
                    "configuration_hash": source["configuration_hash"],
                    "system_prompt_version_id": str(source["system_prompt_version_id"]),
                    "rag_prompt_version_id": str(source["rag_prompt_version_id"]),
                    "retrieval": source["retrieval_configuration"],
                    "generation": source["generation_configuration"],
                }
                cursor = await db.execute(
                    "insert into ragapp.assistant_revisions(project_id,assistant_id,version,"
                    "index_specification_id,created_by,experiment_variant_run_id,configuration) "
                    "values(%s,%s,1,%s,%s,%s,%s) returning id",
                    (project_id, assistant["id"], source["index_specification_id"], created_by,
                     experiment_variant_run_id, Jsonb(configuration)),
                )
                revision = await cursor.fetchone()
                await db.execute(
                    "update ragapp.assistants set active_revision_id=%s where id=%s",
                    (revision["id"], assistant["id"]),
                )
        created = await self.get(assistant["id"], created_by)
        if not created:
            raise RuntimeError("Created assistant could not be loaded")
        return created

    async def completed_run_candidates(self, project_id) -> list[dict]:
        async with self.connect() as db:
            cursor = await db.execute(
                "select evr.id variant_run_id,evr.run_id,e.id experiment_id,e.name experiment_name,"
                "ev.id variant_id,ev.name variant_name,evr.completed_at,"
                "coalesce(evr.aggregate_metrics,'{}'::jsonb) aggregate_metrics "
                "from ragapp.experiment_variant_runs evr "
                "join ragapp.experiment_variants ev on ev.id=evr.variant_id "
                "join ragapp.experiments e on e.id=ev.experiment_id "
                "where evr.project_id=%s and evr.status='completed' "
                "order by evr.completed_at desc",
                (project_id,),
            )
            return await cursor.fetchall()

    async def lineage(self, bot_id, project_id) -> dict | None:
        async with self.connect() as db:
            cursor = await db.execute(
                "select b.id assistant_id,b.name assistant_name,ar.id revision_id,ar.version revision_version,"
                "ar.created_at revision_created_at,ar.configuration revision_configuration,"
                "e.id experiment_id,e.name experiment_name,e.hypothesis,"
                "er.id run_id,er.code_revision,er.created_at run_created_at,er.completed_at run_completed_at,"
                "evr.id variant_run_id,evr.aggregate_metrics,ev.id variant_id,ev.name variant_name,"
                "ev.configuration_hash,s.id index_id,s.configuration index_configuration,"
                "spv.id system_prompt_version_id,sp.name system_prompt_name,spv.version system_prompt_version,"
                "rpv.id rag_prompt_version_id,rp.name rag_prompt_name,rpv.version rag_prompt_version "
                "from ragapp.assistants b join ragapp.assistant_revisions ar on ar.id=b.active_revision_id "
                "join ragapp.experiment_variant_runs evr on evr.id=ar.experiment_variant_run_id "
                "join ragapp.experiment_runs er on er.id=evr.run_id "
                "join ragapp.experiment_variants ev on ev.id=evr.variant_id "
                "join ragapp.experiments e on e.id=ev.experiment_id "
                "join ragapp.specifications s on s.id=ar.index_specification_id "
                "join ragapp.prompt_versions spv on spv.id=(ar.configuration->>'system_prompt_version_id')::uuid "
                "join ragapp.prompts sp on sp.id=spv.prompt_id "
                "join ragapp.prompt_versions rpv on rpv.id=(ar.configuration->>'rag_prompt_version_id')::uuid "
                "join ragapp.prompts rp on rp.id=rpv.prompt_id "
                "where b.id=%s and b.project_id=%s and b.deleted_at is null",
                (bot_id, project_id),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return {
            "assistant": {"id": row["assistant_id"], "name": row["assistant_name"]},
            "revision": {"id": row["revision_id"], "version": row["revision_version"], "created_at": row["revision_created_at"], "configuration": row["revision_configuration"]},
            "experiment": {"id": row["experiment_id"], "name": row["experiment_name"], "hypothesis": row["hypothesis"]},
            "run": {"id": row["run_id"], "variant_run_id": row["variant_run_id"], "code_revision": row["code_revision"], "created_at": row["run_created_at"], "completed_at": row["run_completed_at"], "metrics": row["aggregate_metrics"] or {}},
            "variant": {"id": row["variant_id"], "name": row["variant_name"], "configuration_hash": row["configuration_hash"]},
            "index": {"id": row["index_id"], "configuration": row["index_configuration"]},
            "system_prompt": {"version_id": row["system_prompt_version_id"], "name": row["system_prompt_name"], "version": row["system_prompt_version"]},
            "rag_prompt": {"version_id": row["rag_prompt_version_id"], "name": row["rag_prompt_name"], "version": row["rag_prompt_version"]},
        }

    async def runtime_configuration(self, bot_id, project_id) -> dict | None:
        async with self.connect() as db:
            cursor = await db.execute(
                "select ar.index_specification_id,ar.configuration,"
                "s.configuration index_configuration,em.id embedding_model_id,"
                "coalesce(s.configuration#>>'{knowledge,knowledge_base_id}',scope.knowledge_base_id::text) knowledge_base_id,"
                "spv.template system_prompt,rpv.template rag_prompt "
                "from ragapp.assistants b join ragapp.assistant_revisions ar on ar.id=b.active_revision_id "
                "join ragapp.specifications s on s.id=ar.index_specification_id "
                "join ragapp.embedding_models em on "
                "(em.id=(s.configuration#>>'{embedding,model_id}')::uuid or "
                "((s.configuration#>>'{embedding,model_id}') is null "
                "and em.provider=s.configuration#>>'{embedding,provider}' "
                "and em.model_name=s.configuration#>>'{embedding,model}' "
                "and em.dimensions=(s.configuration#>>'{embedding,dimensions}')::int)) "
                "left join lateral (select c.knowledge_base_id from ragapp.chunks c "
                "where c.specification_id=s.id order by c.created_at limit 1) scope on true "
                "join ragapp.prompt_versions spv on spv.id=(ar.configuration->>'system_prompt_version_id')::uuid "
                "join ragapp.prompt_versions rpv on rpv.id=(ar.configuration->>'rag_prompt_version_id')::uuid "
                "where b.id=%s and b.project_id=%s and b.status='active' and b.deleted_at is null",
                (bot_id, project_id),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        index = row["index_configuration"]
        revision = row["configuration"]
        return {
            "index_specification_id": row["index_specification_id"],
            "knowledge_base_id": row["knowledge_base_id"],
            "embedding_model_id": row["embedding_model_id"],
            "embedding": index["embedding"],
            "retrieval": revision["retrieval"],
            "generation": revision["generation"],
            "system_prompt": row["system_prompt"],
            "rag_prompt": row["rag_prompt"],
        }

    async def get(self, bot_id, user_id) -> KnowledgeBot | None:
        async with self.connect() as db:
            cursor = await db.execute(
                self.select() +
                "join ragapp.project_members pm on pm.project_id=b.project_id "
                "where b.id=%s and pm.user_id=%s and b.deleted_at is null",
                (bot_id, user_id),
            )
            row = await cursor.fetchone()
        return self.model(row) if row else None

    async def list_for_project(self, project_id, user_id) -> list[KnowledgeBot]:
        async with self.connect() as db:
            cursor = await db.execute(
                self.select() +
                "join ragapp.project_members pm on pm.project_id=b.project_id "
                "where b.project_id=%s and pm.user_id=%s and b.deleted_at is null "
                "order by b.updated_at desc",
                (project_id, user_id),
            )
            rows = await cursor.fetchall()
        return [self.model(row) for row in rows]

    async def update(self, bot_id, name, description, update_description, bot_status):
        async with self.connect() as db:
            cursor = await db.execute(
                "update ragapp.assistants set name=coalesce(%s,name), "
                "description=case when %s then %s else description end, "
                "status=coalesce(%s,status) where id=%s and deleted_at is null returning *",
                (
                    name,
                    update_description,
                    description,
                    bot_status.value if bot_status else None,
                    bot_id,
                ),
            )
            row = await cursor.fetchone()
        return self.model(row)

    async def delete(self, bot_id) -> None:
        async with self.connect() as db:
            async with db.transaction():
                await db.execute(
                    "update ragapp.conversations set deleted_at=now() "
                    "where assistant_id=%s and deleted_at is null",
                    (bot_id,),
                )
                await db.execute(
                    "update ragapp.assistants set deleted_at=now() "
                    "where id=%s and deleted_at is null",
                    (bot_id,),
                )
