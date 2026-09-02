import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class ExperimentRepository:
    def __init__(self, database_url):
        self.database_url = database_url

    def can_access(self, project_id, user_id, action="view"):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select ragapp.has_project_permission(%s,%s,'experiments',%s)",
                (project_id, user_id, action),
            ).fetchone()[0]

    def catalog(self, project_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            experiments = db.execute(
                "select e.*,b.name benchmark_name,b.version benchmark_version,"
                "jsonb_array_length(b.content) benchmark_cases,count(v.id) variant_count "
                "from ragapp.experiments e join ragapp.benchmark_datasets b on b.id=e.benchmark_dataset_id "
                "left join ragapp.experiment_variants v on v.experiment_id=e.id "
                "where e.project_id=%s group by e.id,b.name,b.version,b.content order by e.updated_at desc",
                (project_id,),
            ).fetchall()
            datasets = db.execute(
                "select distinct on(lower(name)) id,name,version,jsonb_array_length(content) example_count "
                "from ragapp.benchmark_datasets where project_id=%s order by lower(name),version desc",
                (project_id,),
            ).fetchall()
            indexes = db.execute(
                "select s.id,s.configuration,s.configuration_hash,s.created_at,"
                "count(j.id) job_count,count(j.id) filter(where j.status='completed') completed_jobs "
                "from ragapp.specifications s left join ragapp.ingestion_jobs j on j.specification_id=s.id "
                "where s.project_id=%s and s.kind='pipeline' and not exists("
                "select 1 from ragapp.index_retirements r where r.specification_id=s.id) "
                "group by s.id order by s.created_at desc",
                (project_id,),
            ).fetchall()
            prompts = db.execute(
                "select p.id prompt_id,p.name,p.purpose,p.prompt_type,v.id version_id,v.version "
                "from ragapp.prompts p join lateral(select id,version from ragapp.prompt_versions "
                "where prompt_id=p.id order by version desc limit 1)v on true "
                "where p.project_id=%s and p.status='active' order by p.prompt_type,p.name",
                (project_id,),
            ).fetchall()
        return {
            "experiments": experiments,
            "datasets": datasets,
            "indexes": indexes,
            "prompts": prompts,
        }

    def dataset_exists(self, project_id, dataset_id):
        with psycopg.connect(self.database_url) as db:
            return db.execute(
                "select exists(select 1 from ragapp.benchmark_datasets where id=%s and project_id=%s)",
                (dataset_id, project_id),
            ).fetchone()[0]

    def create_experiment(
        self,
        project_id,
        user_id,
        name,
        description,
        hypothesis,
        dataset_id,
        metrics,
        primary_metric,
    ):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "insert into ragapp.experiments(project_id,name,description,hypothesis,"
                "benchmark_dataset_id,metrics,primary_metric,created_by) "
                "values(%s,%s,%s,%s,%s,%s,%s,%s) returning *",
                (
                    project_id,
                    name,
                    description,
                    hypothesis,
                    dataset_id,
                    Jsonb(metrics),
                    primary_metric,
                    user_id,
                ),
            ).fetchone()

    def detail(self, project_id, experiment_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            experiment = db.execute(
                "select e.*,b.name benchmark_name,b.version benchmark_version,"
                "jsonb_array_length(b.content) benchmark_cases,b.content_sha256 benchmark_hash "
                "from ragapp.experiments e join ragapp.benchmark_datasets b on b.id=e.benchmark_dataset_id "
                "where e.id=%s and e.project_id=%s",
                (experiment_id, project_id),
            ).fetchone()
            if not experiment:
                return None
            variants = db.execute(
                "select v.*,s.configuration index_configuration,sp.name system_prompt_name,"
                "spv.version system_prompt_version,rp.name rag_prompt_name,rpv.version rag_prompt_version "
                "from ragapp.experiment_variants v "
                "join ragapp.specifications s on s.id=v.index_specification_id "
                "join ragapp.prompt_versions spv on spv.id=v.system_prompt_version_id "
                "join ragapp.prompts sp on sp.id=spv.prompt_id "
                "join ragapp.prompt_versions rpv on rpv.id=v.rag_prompt_version_id "
                "join ragapp.prompts rp on rp.id=rpv.prompt_id "
                "where v.experiment_id=%s order by v.created_at",
                (experiment_id,),
            ).fetchall()
        return {"experiment": experiment, "variants": variants}

    def variant_assets(
        self, project_id, experiment_id, index_id, system_version_id, rag_version_id
    ):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            experiment = db.execute(
                "select metrics from ragapp.experiments where id=%s and project_id=%s and status<>'archived'",
                (experiment_id, project_id),
            ).fetchone()
            index = db.execute(
                "select id from ragapp.specifications where id=%s and project_id=%s and kind='pipeline' "
                "and not exists(select 1 from ragapp.index_retirements where specification_id=%s)",
                (index_id, project_id, index_id),
            ).fetchone()
            system = db.execute(
                "select v.id from ragapp.prompt_versions v join ragapp.prompts p on p.id=v.prompt_id "
                "where v.id=%s and v.project_id=%s and p.prompt_type='system' and p.status='active'",
                (system_version_id, project_id),
            ).fetchone()
            rag = db.execute(
                "select v.id from ragapp.prompt_versions v join ragapp.prompts p on p.id=v.prompt_id "
                "where v.id=%s and v.project_id=%s and p.prompt_type='rag_answer' and p.status='active'",
                (rag_version_id, project_id),
            ).fetchone()
            evaluators = db.execute(
                "select distinct on(p.purpose) p.purpose,v.id version_id,v.version,p.name "
                "from ragapp.prompts p join ragapp.prompt_versions v on v.prompt_id=p.id "
                "where p.project_id=%s and p.prompt_type='evaluation' and p.status='active' "
                "order by p.purpose,v.version desc",
                (project_id,),
            ).fetchall()
        return experiment, index, system, rag, evaluators

    def create_variant(
        self,
        project_id,
        experiment_id,
        user_id,
        name,
        index_id,
        system_version_id,
        rag_version_id,
        evaluators,
        retrieval,
        generation,
        configuration_hash,
    ):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            variant = db.execute(
                "insert into ragapp.experiment_variants(project_id,experiment_id,name,"
                "index_specification_id,system_prompt_version_id,rag_prompt_version_id,"
                "evaluator_prompt_versions,retrieval_configuration,generation_configuration,"
                "configuration_hash,created_by) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *",
                (
                    project_id,
                    experiment_id,
                    name,
                    index_id,
                    system_version_id,
                    rag_version_id,
                    Jsonb(evaluators),
                    Jsonb(retrieval),
                    Jsonb(generation),
                    configuration_hash,
                    user_id,
                ),
            ).fetchone()
            db.execute(
                "update ragapp.experiments set status='ready' where id=%s and status='draft'",
                (experiment_id,),
            )
        return variant

    def delete_variant(self, project_id, experiment_id, variant_id):
        with psycopg.connect(self.database_url) as db:
            variant = db.execute(
                "select exists(select 1 from ragapp.experiment_variants "
                "where id=%s and experiment_id=%s and project_id=%s)",
                (variant_id, experiment_id, project_id),
            ).fetchone()[0]
            if not variant:
                return "missing"
            used = db.execute(
                "select exists(select 1 from ragapp.experiment_variant_runs where variant_id=%s)",
                (variant_id,),
            ).fetchone()[0]
            if used:
                return "used"
            db.execute(
                "delete from ragapp.experiment_variants "
                "where id=%s and experiment_id=%s and project_id=%s",
                (variant_id, experiment_id, project_id),
            )
            return "deleted"
