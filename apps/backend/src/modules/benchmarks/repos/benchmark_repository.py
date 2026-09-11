from integrations.database import db_connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class BenchmarkRepository:
    def __init__(self, database_url):
        self.database_url = database_url

    def can_access(self, project_id, user_id, action="view"):
        with db_connection(self.database_url) as db:
            return db.execute(
                "select ragapp.has_project_permission(%s,%s,'benchmarks',%s)",
                (project_id, user_id, action),
            ).fetchone()[0]

    def list(self, project_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select distinct on (lower(name)) id,project_id,name,description,version,"
                "jsonb_array_length(content) example_count,content_sha256,created_by,created_at,"
                "count(*) over(partition by lower(name)) version_count "
                "from ragapp.benchmark_datasets where project_id=%s "
                "order by lower(name),version desc",
                (project_id,),
            ).fetchall()

    def create(
        self,
        project_id,
        user_id,
        name,
        description,
        content,
        content_sha256,
    ):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "insert into ragapp.benchmark_datasets"
                "(project_id,name,description,version,content,content_sha256,created_by) "
                "values(%s,%s,%s,1,%s,%s,%s) returning *",
                (
                    project_id,
                    name,
                    description,
                    Jsonb(content),
                    content_sha256,
                    user_id,
                ),
            ).fetchone()

    def detail(self, project_id, dataset_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            dataset = db.execute(
                "select * from ragapp.benchmark_datasets where id=%s and project_id=%s",
                (dataset_id, project_id),
            ).fetchone()
            if not dataset:
                return None
            versions = db.execute(
                "select id,version,description,jsonb_array_length(content) example_count,"
                "content_sha256,created_by,created_at "
                "from ragapp.benchmark_datasets where project_id=%s and lower(name)=lower(%s) "
                "order by version desc",
                (project_id, dataset["name"]),
            ).fetchall()
        return {"dataset": dataset, "versions": versions}

    def add_version(
        self,
        project_id,
        dataset_id,
        user_id,
        description,
        content,
        content_sha256,
    ):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "insert into ragapp.benchmark_datasets"
                "(project_id,name,description,version,content,content_sha256,created_by) "
                "select project_id,name,coalesce(%s,description),"
                "(select max(version)+1 from ragapp.benchmark_datasets versions "
                "where versions.project_id=source.project_id and lower(versions.name)=lower(source.name)),"
                "%s,%s,%s from ragapp.benchmark_datasets source "
                "where source.id=%s and source.project_id=%s returning *",
                (
                    description,
                    Jsonb(content),
                    content_sha256,
                    user_id,
                    dataset_id,
                    project_id,
                ),
            ).fetchone()
