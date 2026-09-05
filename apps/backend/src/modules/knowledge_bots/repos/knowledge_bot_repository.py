from modules.knowledge_bots.models.models import KnowledgeBot, KnowledgeBotStatus
from psycopg.rows import dict_row
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
        )

    async def create(self, project_id, created_by, name, description) -> KnowledgeBot:
        async with self.connect() as db:
            async with db.transaction():
                cursor = await db.execute(
                    "insert into ragapp.assistants(project_id,created_by,name,description) "
                    "values(%s,%s,%s,%s) returning *",
                    (project_id, created_by, name, description),
                )
                row = await cursor.fetchone()
        return self.model(row)

    async def get(self, bot_id, user_id) -> KnowledgeBot | None:
        async with self.connect() as db:
            cursor = await db.execute(
                "select b.* from ragapp.assistants b "
                "join ragapp.project_members pm on pm.project_id=b.project_id "
                "where b.id=%s and pm.user_id=%s and b.deleted_at is null",
                (bot_id, user_id),
            )
            row = await cursor.fetchone()
        return self.model(row) if row else None

    async def list_for_project(self, project_id, user_id) -> list[KnowledgeBot]:
        async with self.connect() as db:
            cursor = await db.execute(
                "select b.* from ragapp.assistants b "
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
