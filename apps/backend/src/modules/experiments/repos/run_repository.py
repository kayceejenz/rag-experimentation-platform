import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from integrations.database import db_connection


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

    def claim(self, worker, lease_seconds=900):
        with db_connection(self.url, row_factory=dict_row) as db:
            return db.execute(
                "update ragapp.experiment_runs set status='running',"
                "started_at=coalesce(started_at,now()),heartbeat_at=now(),worker_id=%s,attempt=attempt+1 "
                "where id=(select id from ragapp.experiment_runs "
                "where status='pending' or (status='running' and (heartbeat_at is null "
                "or heartbeat_at < now()-(%s*interval '1 second'))) "
                "order by created_at for update skip locked limit 1) returning *",
                (worker, lease_seconds),
            ).fetchone()

    def heartbeat(self, run_id, worker):
        with db_connection(self.url) as db:
            db.execute(
                "update ragapp.experiment_runs set heartbeat_at=now() "
                "where id=%s and worker_id=%s and status='running'",
                (run_id, worker),
            )

    def payload(self, run_id):
        with db_connection(self.url, row_factory=dict_row) as db:
            run = db.execute(
                "select r.*,e.metrics,e.benchmark_dataset_id,b.content from ragapp.experiment_runs r join ragapp.experiments e on e.id=r.experiment_id join ragapp.benchmark_datasets b on b.id=e.benchmark_dataset_id where r.id=%s",
                (run_id,),
            ).fetchone()
            variants = db.execute(
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
            ).fetchall()
            for v in variants:
                ids = list(v["evaluator_prompt_versions"].values())
                rows = (
                    db.execute(
                        "select p.purpose,pv.template from ragapp.prompt_versions pv join ragapp.prompts p on p.id=pv.prompt_id where pv.id=any(%s::uuid[])",
                        (ids,),
                    ).fetchall()
                    if ids
                    else []
                )
                v["evaluators"] = {x["purpose"]: x["template"] for x in rows}
            return run, variants

    def start_variant(self, id):
        with db_connection(self.url) as db:
            db.execute(
                "update ragapp.experiment_variant_runs set status='running',"
                "started_at=coalesce(started_at,now()),completed_at=null,error_message=null where id=%s",
                (id,),
            )

    def completed_cases(self, variant_run_id):
        with db_connection(self.url, row_factory=dict_row) as db:
            return db.execute(
                "select case_id,metrics from ragapp.experiment_case_results "
                "where variant_run_id=%s and error_message is null",
                (variant_run_id,),
            ).fetchall()

    def save_case(
        self, variant_run_id, case, position, context, answer, metrics, error=None
    ):
        with db_connection(self.url) as db:
            db.execute(
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

    def finish_variant(self, id, metrics, error=None):
        with db_connection(self.url) as db:
            db.execute(
                "update ragapp.experiment_variant_runs set status=%s,aggregate_metrics=%s,error_message=%s,completed_at=now() where id=%s",
                ("failed" if error else "completed", Jsonb(metrics), error, id),
            )

    def finish(self, id, error=None):
        with db_connection(self.url) as db:
            db.execute(
                "update ragapp.experiment_runs set status=%s,error_message=%s,"
                "completed_at=now(),heartbeat_at=now() where id=%s",
                ("failed" if error else "completed", error, id),
            )
