import psycopg
from psycopg.rows import dict_row

from modules.chats.models.chat_model import Chat, ChatStatus


class ChatRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def chat(row) -> Chat:
        return Chat(
            id=row["id"],
            project_id=row["project_id"],
            created_by=row["created_by"],
            title=row["title"],
            status=ChatStatus(row["status"]),
            knowledge_base_id=row["knowledge_base_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create(self, project_id, created_by, title):
        with self.connect() as db:
            chat = db.execute(
                "insert into ragapp.chats(project_id,created_by,title) "
                "values(%s,%s,%s) returning *",
                (project_id, created_by, title),
            ).fetchone()

            knowledge_base = db.execute(
                "insert into ragapp.knowledge_bases(project_id,chat_id) values(%s,%s) returning id",
                (project_id, chat["id"]),
            ).fetchone()

            chat["knowledge_base_id"] = knowledge_base["id"]
        return self.chat(chat)

    def get(self, chat_id, user_id):
        with self.connect() as db:
            row = db.execute(
                "select c.*,kb.id as knowledge_base_id from ragapp.chats c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "join ragapp.knowledge_bases kb on kb.chat_id=c.id "
                "where c.id=%s and pm.user_id=%s and c.deleted_at is null "
                "and kb.deleted_at is null",
                (chat_id, user_id),
            ).fetchone()
        return self.chat(row) if row else None

    def list_for_project(self, project_id, user_id):
        with self.connect() as db:
            rows = db.execute(
                "select c.*,kb.id as knowledge_base_id from ragapp.chats c "
                "join ragapp.project_members pm on pm.project_id=c.project_id "
                "join ragapp.knowledge_bases kb on kb.chat_id=c.id "
                "where c.project_id=%s and pm.user_id=%s and c.deleted_at is null "
                "and kb.deleted_at is null order by c.updated_at desc",
                (project_id, user_id),
            ).fetchall()
        return [self.chat(row) for row in rows]

    def update(self, chat_id, title, chat_status):
        with self.connect() as db:
            row = db.execute(
                "update ragapp.chats set title=coalesce(%s,title), "
                "status=coalesce(%s,status) where id=%s and deleted_at is null returning *",
                (title, chat_status.value if chat_status else None, chat_id),
            ).fetchone()
            knowledge_base = db.execute(
                "select id from ragapp.knowledge_bases where chat_id=%s and deleted_at is null",
                (chat_id,),
            ).fetchone()
            row["knowledge_base_id"] = knowledge_base["id"]
        return self.chat(row)

    def delete(self, chat_id):
        with self.connect() as db:
            db.execute(
                "update ragapp.chats set deleted_at=now() where id=%s and deleted_at is null",
                (chat_id,),
            )
            db.execute(
                "update ragapp.knowledge_bases set deleted_at=now() "
                "where chat_id=%s and deleted_at is null",
                (chat_id,),
            )
