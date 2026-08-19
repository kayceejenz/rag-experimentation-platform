from psycopg import AsyncConnection
from psycopg.rows import dict_row

from modules.projects.models.project_model import Project, ProjectAccess, ProjectRole


class ProjectRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def connect(self):
        return await AsyncConnection.connect(self.database_url, row_factory=dict_row)

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

    async def create(self, owner_id, name, description):
        async with await self.connect() as db:
            curr = await db.execute(
                "insert into ragapp.projects(owner_id,name,description) "
                "values(%s,%s,%s) returning *",
                (owner_id, name, description),
            )
            row = await curr.fetchone()
        return self.project(row)

    async def get_access(self, project_id, user_id):
        async with await self.connect() as db:
            curr = await db.execute(
                "select p.*,m.role from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "where p.id=%s and m.user_id=%s and p.deleted_at is null",
                (project_id, user_id),
            )
            row = await curr.fetchone()
        return ProjectAccess(self.project(row), ProjectRole(row["role"])) if row else None

    async def list_for_user(self, user_id):
        async with await self.connect() as db:
            curr = await db.execute(
                "select p.*,m.role from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "where m.user_id=%s and p.deleted_at is null order by p.updated_at desc",
                (user_id,),
            )
            rows = await curr.fetchall()
        return [ProjectAccess(self.project(row), ProjectRole(row["role"])) for row in rows]

    async def update(self, project_id, name, description, update_description):
        async with await self.connect() as db:
            curr = await db.execute(
                "update ragapp.projects set name=coalesce(%s,name), "
                "description=case when %s then %s else description end "
                "where id=%s and deleted_at is null returning *",
                (name, update_description, description, project_id),
            )
            row = await curr.fetchone()
        return self.project(row)

    async def delete(self, project_id):
        async with await self.connect() as db:
            await db.execute("update ragapp.projects set deleted_at=now() where id=%s", (project_id,))
