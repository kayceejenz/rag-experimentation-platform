import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

class ExperimentRunRepository:
    def __init__(self,url): self.url=url
    def enqueue(self,project_id,experiment_id,user_id,revision,generation_models=()):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            variants=db.execute(
                "select id from ragapp.experiment_variants where experiment_id=%s "
                "and (cardinality(%s::text[])=0 or generation_configuration->>'model'=any(%s::text[]))",
                (experiment_id,list(generation_models),list(generation_models)),
            ).fetchall()
            if len(variants)<2:
                raise ValueError(
                    "Add at least two variants using an enabled generation model before running the experiment"
                )
            run=db.execute("insert into ragapp.experiment_runs(project_id,experiment_id,code_revision,created_by) values(%s,%s,%s,%s) returning *",(project_id,experiment_id,revision,user_id)).fetchone()
            for variant in variants: db.execute("insert into ragapp.experiment_variant_runs(run_id,variant_id,project_id) values(%s,%s,%s)",(run['id'],variant['id'],project_id))
            return run
    def runs(self,experiment_id):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            return db.execute("select r.*,count(v.id) variant_count,count(v.id) filter(where v.status='completed') completed_variants from ragapp.experiment_runs r left join ragapp.experiment_variant_runs v on v.run_id=r.id where r.experiment_id=%s group by r.id order by r.created_at desc",(experiment_id,)).fetchall()
    def run_detail(self,project_id,run_id):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            run=db.execute("select * from ragapp.experiment_runs where id=%s and project_id=%s",(run_id,project_id)).fetchone()
            if not run:return None
            variants=db.execute("select vr.*,v.name,v.configuration_hash from ragapp.experiment_variant_runs vr join ragapp.experiment_variants v on v.id=vr.variant_id where vr.run_id=%s order by v.created_at",(run_id,)).fetchall()
            cases=db.execute("select c.* from ragapp.experiment_case_results c join ragapp.experiment_variant_runs vr on vr.id=c.variant_run_id where vr.run_id=%s order by vr.id,c.position",(run_id,)).fetchall()
            return {'run':run,'variants':variants,'cases':cases}
    def claim(self,worker):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            return db.execute("update ragapp.experiment_runs set status='running',started_at=now(),worker_id=%s where id=(select id from ragapp.experiment_runs where status='pending' order by created_at for update skip locked limit 1) returning *",(worker,)).fetchone()
    def payload(self,run_id):
        with psycopg.connect(self.url,row_factory=dict_row) as db:
            run=db.execute("select r.*,e.metrics,e.benchmark_dataset_id,b.content from ragapp.experiment_runs r join ragapp.experiments e on e.id=r.experiment_id join ragapp.benchmark_datasets b on b.id=e.benchmark_dataset_id where r.id=%s",(run_id,)).fetchone()
            variants=db.execute("select vr.id variant_run_id,v.*,s.configuration index_configuration,"
                "coalesce(s.configuration#>>'{knowledge,knowledge_base_id}',(select src.knowledge_base_id::text "
                "from ragapp.ingestion_jobs j join ragapp.source_versions sv on sv.id=j.source_version_id "
                "join ragapp.sources src on src.id=sv.source_id where j.specification_id=s.id "
                "order by j.created_at limit 1)) knowledge_base_id,"
                "spv.template system_template,rpv.template rag_template "
                "from ragapp.experiment_variant_runs vr join ragapp.experiment_variants v on v.id=vr.variant_id "
                "join ragapp.specifications s on s.id=v.index_specification_id "
                "join ragapp.prompt_versions spv on spv.id=v.system_prompt_version_id "
                "join ragapp.prompt_versions rpv on rpv.id=v.rag_prompt_version_id "
                "where vr.run_id=%s order by v.created_at",(run_id,)).fetchall()
            for v in variants:
                ids=list(v['evaluator_prompt_versions'].values())
                rows=db.execute("select p.purpose,pv.template from ragapp.prompt_versions pv join ragapp.prompts p on p.id=pv.prompt_id where pv.id=any(%s::uuid[])",(ids,)).fetchall() if ids else []
                v['evaluators']={x['purpose']:x['template'] for x in rows}
            return run,variants
    def start_variant(self,id):
        with psycopg.connect(self.url) as db:db.execute("update ragapp.experiment_variant_runs set status='running',started_at=now() where id=%s",(id,))
    def save_case(self,variant_run_id,case,position,context,answer,metrics,error=None):
        with psycopg.connect(self.url) as db:db.execute("insert into ragapp.experiment_case_results(variant_run_id,case_id,position,question,reference_answer,retrieved_context,generated_answer,metrics,error_message) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(variant_run_id,case['case_id'],position,case['question'],case.get('reference_answer'),Jsonb(context),answer,Jsonb(metrics),error))
    def finish_variant(self,id,metrics,error=None):
        with psycopg.connect(self.url) as db:db.execute("update ragapp.experiment_variant_runs set status=%s,aggregate_metrics=%s,error_message=%s,completed_at=now() where id=%s",('failed' if error else 'completed',Jsonb(metrics),error,id))
    def finish(self,id,error=None):
        with psycopg.connect(self.url) as db:db.execute("update ragapp.experiment_runs set status=%s,error_message=%s,completed_at=now() where id=%s",('failed' if error else 'completed',error,id))
