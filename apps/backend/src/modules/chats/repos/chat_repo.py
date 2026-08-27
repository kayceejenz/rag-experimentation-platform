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
            bot_id=row["bot_id"],
            project_id=row["project_id"],
            created_by=row["created_by"],
            title=row["title"],
            status=ChatStatus(row["status"]),
            knowledge_base_id=row["knowledge_base_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, project_id, created_by, title) -> Chat:
        async with await self.connect() as db:
            async with db.transaction():
                bot_cur = await db.execute(
                    "insert into ragapp.knowledge_bots(project_id,created_by,name) "
                    "values(%s,%s,%s) returning id",
                    (project_id, created_by, title),
                )
                bot = await bot_cur.fetchone()
                cur = await db.execute(
                    "insert into ragapp.chats(project_id,bot_id,created_by,title) "
                    "values(%s,%s,%s,%s) returning *",
                    (project_id, bot["id"], created_by, title),
                )
                chat = await cur.fetchone()

                kb_cur = await db.execute(
                    "insert into ragapp.knowledge_bases(project_id,bot_id,chat_id) "
                    "values(%s,%s,%s) returning id",
                    (project_id, bot["id"], chat["id"]),
                )
                knowledge_base = await kb_cur.fetchone()

                chat["knowledge_base_id"] = knowledge_base["id"]
        return self.chat(chat)

    async def get(self, chat_id, user_id) -> Chat | None:
        async with await self.connect() as db:
            cur = await db.execute(
                "select c.*,kb.id as knowledge_base_id from ragapp.chats c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "join ragapp.knowledge_bases kb on kb.chat_id=c.id "
                "where c.id=%s and pm.user_id=%s and c.deleted_at is null "
                "and kb.deleted_at is null",
                (chat_id, user_id),
            )
            row = await cur.fetchone()
        return self.chat(row) if row else None

    async def list_for_project(self, project_id, user_id) -> list[Chat]:
        async with await self.connect() as db:
            cur = await db.execute(
                "select c.*,kb.id as knowledge_base_id from ragapp.chats c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "join ragapp.knowledge_bases kb on kb.chat_id=c.id "
                "where c.project_id=%s and pm.user_id=%s and c.deleted_at is null "
                "and kb.deleted_at is null order by c.updated_at desc",
                (project_id, user_id),
            )
            rows = await cur.fetchall()
        return [self.chat(row) for row in rows]

    async def update(self, chat_id, title, chat_status) -> Chat:
        async with await self.connect() as db:
            async with db.transaction():
                cur = await db.execute(
                    "update ragapp.chats set title=coalesce(%s,title), "
                    "status=coalesce(%s,status) where id=%s and deleted_at is null returning *",
                    (title, chat_status.value if chat_status else None, chat_id),
                )
                row = await cur.fetchone()

                kb_cur = await db.execute(
                    "select id from ragapp.knowledge_bases where bot_id=%s and deleted_at is null",
                    (row["bot_id"],),
                )
                knowledge_base = await kb_cur.fetchone()
                row["knowledge_base_id"] = knowledge_base["id"]
        return self.chat(row)

    async def delete(self, chat_id) -> None:
        async with await self.connect() as db:
            async with db.transaction():
                await db.execute(
                    "update ragapp.chats set deleted_at=now() where id=%s and deleted_at is null",
                    (chat_id,),
                )
                await db.execute(
                    "update ragapp.knowledge_bases set deleted_at=now() "
                    "where bot_id=(select bot_id from ragapp.chats where id=%s) "
                    "and deleted_at is null",
                    (chat_id,),
                )
                await db.execute(
                    "update ragapp.knowledge_bots set deleted_at=now() "
                    "where id=(select bot_id from ragapp.chats where id=%s) "
                    "and deleted_at is null",
                    (chat_id,),
                )
