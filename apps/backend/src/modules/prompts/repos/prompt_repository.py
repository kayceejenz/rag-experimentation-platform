import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from integrations.database import db_connection


class PromptRepository:
    def __init__(self, database_url):
        self.database_url = database_url

    def can_access(self, project_id, user_id, action="view"):
        with db_connection(self.database_url) as db:
            return db.execute(
                "select ragapp.has_project_permission(%s,%s,'prompts',%s)",
                (project_id, user_id, action),
            ).fetchone()[0]

    def list(self, project_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            return db.execute(
                "select p.*,v.id latest_version_id,v.version latest_version,v.variables,v.content_sha256 "
                "from ragapp.prompts p left join lateral(select id,version,variables,content_sha256 from ragapp.prompt_versions "
                "where prompt_id=p.id order by version desc limit 1)v on true where p.project_id=%s "
                "order by case p.prompt_type when 'system' then 1 when 'rag_answer' then 2 else 3 end, "
                "p.origin desc,p.updated_at desc",
                (project_id,),
            ).fetchall()

    def create(
        self,
        project_id,
        user_id,
        name,
        purpose,
        description,
        prompt_type,
        template,
        variables,
        digest,
        change_note,
    ):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            prompt = db.execute(
                "insert into ragapp.prompts(project_id,name,purpose,description,prompt_type,created_by) values(%s,%s,%s,%s,%s,%s) returning *",
                (project_id, name, purpose, description, prompt_type, user_id),
            ).fetchone()
            version = db.execute(
                "insert into ragapp.prompt_versions(prompt_id,project_id,version,template,variables,content_sha256,change_note,created_by) values(%s,%s,1,%s,%s,%s,%s,%s) returning *",
                (
                    prompt["id"],
                    project_id,
                    template,
                    Jsonb(variables),
                    digest,
                    change_note,
                    user_id,
                ),
            ).fetchone()
        return prompt, version

    def detail(self, project_id, prompt_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            prompt = db.execute(
                "select * from ragapp.prompts where id=%s and project_id=%s",
                (prompt_id, project_id),
            ).fetchone()
            if not prompt:
                return None
            versions = db.execute(
                "select * from ragapp.prompt_versions where prompt_id=%s order by version desc",
                (prompt_id,),
            ).fetchall()
        return {"prompt": prompt, "versions": versions}

    def add_version(
        self, project_id, prompt_id, user_id, template, variables, digest, change_note
    ):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "insert into ragapp.prompt_versions(prompt_id,project_id,version,template,variables,content_sha256,change_note,created_by) "
                "select id,project_id,coalesce((select max(version)+1 from ragapp.prompt_versions where prompt_id=%s),1),%s,%s,%s,%s,%s "
                "from ragapp.prompts where id=%s and project_id=%s and status='active' returning *",
                (
                    prompt_id,
                    template,
                    Jsonb(variables),
                    digest,
                    change_note,
                    user_id,
                    prompt_id,
                    project_id,
                ),
            ).fetchone()
            if row:
                db.execute(
                    "update ragapp.prompts set updated_at=now() where id=%s",
                    (prompt_id,),
                )
        return row

    def archive(self, project_id, prompt_id):
        with db_connection(self.database_url) as db:
            return (
                db.execute(
                    "update ragapp.prompts set status='archived' where id=%s and project_id=%s and status='active' returning id",
                    (prompt_id, project_id),
                ).fetchone()
                is not None
            )
