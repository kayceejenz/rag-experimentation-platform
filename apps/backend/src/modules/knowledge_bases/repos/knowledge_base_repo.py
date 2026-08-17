import psycopg
from psycopg.rows import dict_row

from modules.knowledge_bases.models.knowledge_base_model import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def get_for_user(self, knowledge_base_id, user_id):
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select kb.* from ragapp.knowledge_bases kb "
                "join ragapp.project_members pm on pm.project_id=kb.project_id "
                "where kb.id=%s and pm.user_id=%s and kb.deleted_at is null",
                (knowledge_base_id, user_id),
            ).fetchone()
        return self._model(row) if row else None

    @staticmethod
    def _model(row) -> KnowledgeBase:
        return KnowledgeBase(
            id=row["id"],
            project_id=row["project_id"],
            chat_id=row["chat_id"],
            name=row["name"],
            created_at=row["created_at"],
        )
