import psycopg
from psycopg.rows import dict_row

from modules.projects.models.project_model import Project, ProjectAccess, ProjectRole


class ProjectRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def project(row) -> Project:
        return Project(
            row["id"],
            row["owner_id"],
            row["name"],
            row["description"],
            row["created_at"],
            row["updated_at"],
        )

    def create(self, owner_id, name, description):
        with self.connect() as db:
            row = db.execute(
                "insert into ragapp.projects(owner_id,name,description) "
                "values(%s,%s,%s) returning *",
                (owner_id, name, description),
            ).fetchone()
        return self.project(row)

    def get_access(self, project_id, user_id):
        with self.connect() as db:
            row = db.execute(
                "select p.*,m.role from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "where p.id=%s and m.user_id=%s and p.deleted_at is null",
                (project_id, user_id),
            ).fetchone()
        return ProjectAccess(self.project(row), ProjectRole(row["role"])) if row else None

    def list_for_user(self, user_id):
        with self.connect() as db:
            rows = db.execute(
                "select p.*,m.role from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "where m.user_id=%s and p.deleted_at is null order by p.updated_at desc",
                (user_id,),
            ).fetchall()
        return [ProjectAccess(self.project(row), ProjectRole(row["role"])) for row in rows]

    def update(self, project_id, name, description, update_description):
        with self.connect() as db:
            row = db.execute(
                "update ragapp.projects set name=coalesce(%s,name), "
                "description=case when %s then %s else description end "
                "where id=%s and deleted_at is null returning *",
                (name, update_description, description, project_id),
            ).fetchone()
        return self.project(row)

    def delete(self, project_id):
        with self.connect() as db:
            db.execute("update ragapp.projects set deleted_at=now() where id=%s", (project_id,))
