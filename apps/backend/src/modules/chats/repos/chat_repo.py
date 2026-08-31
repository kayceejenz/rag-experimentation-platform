from psycopg import AsyncConnection
from psycopg.rows import dict_row

from modules.chats.models.chat_model import Chat, ChatStatus


class ChatRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def connect(self) -> AsyncConnection:
        return await AsyncConnection.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def chat(row: dict) -> Chat:
        return Chat(
            id=row["id"],
            assistant_id=row["assistant_id"],
            project_id=row["project_id"],
            created_by=row["created_by"],
            title=row["title"],
            status=ChatStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_for_assistant(self, assistant_id, project_id, created_by, title) -> Chat:
        async with await self.connect() as db:
            async with db.transaction():
                cur = await db.execute(
                    "insert into ragapp.conversations(project_id,assistant_id,created_by,title) "
                    "values(%s,%s,%s,%s) returning *",
                    (project_id, assistant_id, created_by, title),
                )
                chat = await cur.fetchone()
        return self.chat(chat)

    async def get(self, chat_id, user_id) -> Chat | None:
        async with await self.connect() as db:
            cur = await db.execute(
                "select c.* from ragapp.conversations c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "where c.id=%s and pm.user_id=%s and c.deleted_at is null "
                "",
                (chat_id, user_id),
            )
            row = await cur.fetchone()
        return self.chat(row) if row else None

    async def list_for_project(self, project_id, user_id) -> list[Chat]:
        async with await self.connect() as db:
            cur = await db.execute(
                "select c.* from ragapp.conversations c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "where c.project_id=%s and pm.user_id=%s and c.deleted_at is null "
                "order by c.updated_at desc",
                (project_id, user_id),
            )
            rows = await cur.fetchall()
        return [self.chat(row) for row in rows]

    async def list_for_assistant(self, assistant_id, user_id) -> list[Chat]:
        async with await self.connect() as db:
            cur = await db.execute(
                "select c.* from ragapp.conversations c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "where c.assistant_id=%s and pm.user_id=%s and c.deleted_at is null "
                "order by c.updated_at desc",
                (assistant_id, user_id),
            )
            rows = await cur.fetchall()
        return [self.chat(row) for row in rows]

    async def update(self, chat_id, title, chat_status) -> Chat:
        async with await self.connect() as db:
            async with db.transaction():
                cur = await db.execute(
                    "update ragapp.conversations set title=coalesce(%s,title), "
                    "status=coalesce(%s,status) where id=%s and deleted_at is null returning *",
                    (title, chat_status.value if chat_status else None, chat_id),
                )
                row = await cur.fetchone()

        return self.chat(row)

    async def delete(self, chat_id) -> None:
        async with await self.connect() as db:
            await db.execute(
                "update ragapp.conversations set deleted_at=now() "
                "where id=%s and deleted_at is null",
                (chat_id,),
            )
