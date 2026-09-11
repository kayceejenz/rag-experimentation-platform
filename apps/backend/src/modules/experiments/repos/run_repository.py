from integrations.database import async_db_connection, db_connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class ExperimentRunRepository:
    def __init__(self, url):
        self.url = url

    def enqueue(
        self,
        project_id,
        experiment_id,
        user_id,
        revision,
        generation_models=(),
        variant_ids=(),
    ):
        with db_connection(self.url, row_factory=dict_row) as db:
            variants = db.execute(
                "select id from ragapp.experiment_variants where experiment_id=%s "
                "and project_id=%s and id=any(%s::uuid[]) "
                "and (cardinality(%s::text[])=0 or generation_configuration->>'model'=any(%s::text[]))",
                (
                    experiment_id,
                    project_id,
                    list(variant_ids),
                    list(generation_models),
                    list(generation_models),
                ),
            ).fetchall()
            selected = {str(value) for value in variant_ids}
            found = {str(variant["id"]) for variant in variants}
            if not selected or found != selected:
                raise ValueError(
                    "Select valid variants using an enabled generation model"
                )
            run = db.execute(
                "insert into ragapp.experiment_runs(project_id,experiment_id,code_revision,created_by) values(%s,%s,%s,%s) returning *",
                (project_id, experiment_id, revision, user_id),
            ).fetchone()
            for variant in variants:
                db.execute(
                    "insert into ragapp.experiment_variant_runs(run_id,variant_id,project_id) values(%s,%s,%s)",
                    (run["id"], variant["id"], project_id),
                )
            return run

    def runs(self, experiment_id):
        with db_connection(self.url, row_factory=dict_row) as db:
            return db.execute(
                "select r.id,r.experiment_id,r.created_at,r.code_revision,r.status run_status,"
                "r.error_message run_error_message,vr.id variant_run_id,vr.variant_id,"
                "vr.status,vr.error_message,vr.aggregate_metrics,vr.completed_at "
                "from ragapp.experiment_runs r join ragapp.experiment_variant_runs vr on vr.run_id=r.id "
                "where r.experiment_id=%s order by r.created_at desc",
                (experiment_id,),
            ).fetchall()

    def project_runs(self, project_id, limit=100):
        with db_connection(self.url, row_factory=dict_row) as db:
            return db.execute(
                "select r.id run_id,r.status run_status,r.code_revision,r.created_at,"
                "r.started_at,r.completed_at,r.error_message run_error_message,"
                "e.id experiment_id,e.name experiment_name,"
                "vr.id variant_run_id,vr.status variant_status,vr.error_message variant_error_message,"
                "vr.aggregate_metrics,v.id variant_id,v.name variant_name,"
                "a.id assistant_id,a.name assistant_name,ar.version assistant_revision "
                "from ragapp.experiment_runs r join ragapp.experiments e on e.id=r.experiment_id "
                "join ragapp.experiment_variant_runs vr on vr.run_id=r.id "
                "join ragapp.experiment_variants v on v.id=vr.variant_id "
                "left join ragapp.assistant_revisions ar on ar.experiment_variant_run_id=vr.id "
                "left join ragapp.assistants a on a.active_revision_id=ar.id and a.deleted_at is null "
                "where r.project_id=%s order by r.created_at desc,v.name limit %s",
                (project_id, limit),
            ).fetchall()

    def run_detail(self, project_id, run_id):
        with db_connection(self.url, row_factory=dict_row) as db:
            run = db.execute(
                "select * from ragapp.experiment_runs where id=%s and project_id=%s",
                (run_id, project_id),
            ).fetchone()
            if not run:
                return None
            variants = db.execute(
                "select vr.*,v.name,v.configuration_hash from ragapp.experiment_variant_runs vr join ragapp.experiment_variants v on v.id=vr.variant_id where vr.run_id=%s order by v.created_at",
                (run_id,),
            ).fetchall()
            cases = db.execute(
                "select c.* from ragapp.experiment_case_results c join ragapp.experiment_variant_runs vr on vr.id=c.variant_run_id where vr.run_id=%s order by vr.id,c.position",
                (run_id,),
            ).fetchall()
            return {"run": run, "variants": variants, "cases": cases}

    async def claim(self, worker, lease_seconds=900):
        async with async_db_connection(self.url, row_factory=dict_row) as db:
            cursor = await db.execute(
                "update ragapp.experiment_runs set status='running',"
                "started_at=coalesce(started_at,now()),heartbeat_at=now(),worker_id=%s,attempt=attempt+1 "
                "where id=(select id from ragapp.experiment_runs "
                "where status='pending' or (status='running' and (heartbeat_at is null "
                "or heartbeat_at < now()-(%s*interval '1 second'))) "
                "order by created_at for update skip locked limit 1) returning *",
                (worker, lease_seconds),
            )
            return await cursor.fetchone()

    async def heartbeat(self, run_id, worker):
        async with async_db_connection(self.url) as db:
            await db.execute(
                "update ragapp.experiment_runs set heartbeat_at=now() "
                "where id=%s and worker_id=%s and status='running'",
                (run_id, worker),
            )

    async def payload(self, run_id):
        async with async_db_connection(self.url, row_factory=dict_row) as db:
            cursor = await db.execute(
                "select r.*,e.metrics,e.benchmark_dataset_id,b.content from ragapp.experiment_runs r join ragapp.experiments e on e.id=r.experiment_id join ragapp.benchmark_datasets b on b.id=e.benchmark_dataset_id where r.id=%s",
                (run_id,),
            )
            run = await cursor.fetchone()
            cursor = await db.execute(
                "select vr.id variant_run_id,vr.status variant_run_status,v.*,s.configuration index_configuration,"
                "coalesce(s.configuration#>>'{embedding,model_id}',(select em.id::text "
                "from ragapp.embedding_models em where em.provider=s.configuration#>>'{embedding,provider}' "
                "and em.model_name=s.configuration#>>'{embedding,model}' "
                "and em.dimensions=(s.configuration#>>'{embedding,dimensions}')::integer limit 1)) embedding_model_id,"
                "coalesce(s.configuration#>>'{embedding,distance_metric}',(select em.distance_metric "
                "from ragapp.embedding_models em where em.provider=s.configuration#>>'{embedding,provider}' "
                "and em.model_name=s.configuration#>>'{embedding,model}' "
                "and em.dimensions=(s.configuration#>>'{embedding,dimensions}')::integer limit 1),'cosine') embedding_distance_metric,"
                "coalesce(s.configuration#>>'{knowledge,knowledge_base_id}',(select src.knowledge_base_id::text "
                "from ragapp.ingestion_jobs j join ragapp.source_versions sv on sv.id=j.source_version_id "
                "join ragapp.sources src on src.id=sv.source_id where j.specification_id=s.id "
                "order by j.created_at limit 1)) knowledge_base_id,"
                "spv.template system_template,rpv.template rag_template "
                "from ragapp.experiment_variant_runs vr join ragapp.experiment_variants v on v.id=vr.variant_id "
                "join ragapp.specifications s on s.id=v.index_specification_id "
                "join ragapp.prompt_versions spv on spv.id=v.system_prompt_version_id "
                "join ragapp.prompt_versions rpv on rpv.id=v.rag_prompt_version_id "
                "where vr.run_id=%s order by v.created_at",
                (run_id,),
            )
            variants = await cursor.fetchall()
            evaluator_ids = {
                evaluator_id
                for variant in variants
                for evaluator_id in variant["evaluator_prompt_versions"].values()
            }
            evaluator_rows = []
            if evaluator_ids:
                cursor = await db.execute(
                    "select pv.id,p.purpose,pv.template from ragapp.prompt_versions pv "
                    "join ragapp.prompts p on p.id=pv.prompt_id "
                    "where pv.id=any(%s::uuid[])",
                    (list(evaluator_ids),),
                )
                evaluator_rows = await cursor.fetchall()
            evaluators_by_id = {
                str(row["id"]): (row["purpose"], row["template"])
                for row in evaluator_rows
            }
            for v in variants:
                v["evaluators"] = {}
                for evaluator_id in v["evaluator_prompt_versions"].values():
                    evaluator = evaluators_by_id.get(str(evaluator_id))
                    if evaluator is not None:
                        purpose, template = evaluator
                        v["evaluators"][purpose] = template
            return run, variants

    async def start_variant(self, id):
        async with async_db_connection(self.url) as db:
            await db.execute(
                "update ragapp.experiment_variant_runs set status='running',"
                "started_at=coalesce(started_at,now()),completed_at=null,error_message=null where id=%s",
                (id,),
            )

    async def completed_cases(self, variant_run_id):
        async with async_db_connection(self.url, row_factory=dict_row) as db:
            cursor = await db.execute(
                "select case_id,metrics from ragapp.experiment_case_results "
                "where variant_run_id=%s and error_message is null",
                (variant_run_id,),
            )
            return await cursor.fetchall()

    async def save_case(
        self, variant_run_id, case, position, context, answer, metrics, error=None
    ):
        async with async_db_connection(self.url) as db:
            await db.execute(
                "insert into ragapp.experiment_case_results(variant_run_id,case_id,position,question,reference_answer,retrieved_context,generated_answer,metrics,error_message) values(%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict(variant_run_id,case_id) do nothing",
                (
                    variant_run_id,
                    case["case_id"],
                    position,
                    case["question"],
                    case.get("reference_answer"),
                    Jsonb(context),
                    answer,
                    Jsonb(metrics),
                    error,
                ),
            )

    async def finish_variant(self, id, metrics, error=None):
        async with async_db_connection(self.url) as db:
            await db.execute(
                "update ragapp.experiment_variant_runs set status=%s,aggregate_metrics=%s,error_message=%s,completed_at=now() where id=%s",
                ("failed" if error else "completed", Jsonb(metrics), error, id),
            )

    async def finish(self, id, error=None):
        async with async_db_connection(self.url) as db:
            await db.execute(
                "update ragapp.experiment_runs set status=%s,error_message=%s,"
                "completed_at=now(),heartbeat_at=now() where id=%s",
                ("failed" if error else "completed", error, id),
            )
