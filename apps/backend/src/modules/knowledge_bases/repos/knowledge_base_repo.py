import psycopg
from modules.knowledge_bases.models.knowledge_base_model import KnowledgeBase
from psycopg.rows import dict_row
from integrations.database import db_connection


class KnowledgeBaseRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def get_for_user(self, knowledge_base_id, user_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select kb.* from ragapp.knowledge_bases kb "
                "where kb.id=%s and ragapp.has_project_permission(kb.project_id,%s,'knowledge','view') "
                "and kb.deleted_at is null",
                (knowledge_base_id, user_id),
            ).fetchone()
        return self._model(row) if row else None

    def get_for_project(self, project_id, user_id):
        with db_connection(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select kb.* from ragapp.project_sources ps "
                "join ragapp.knowledge_bases kb on kb.id=ps.knowledge_base_id "
                "where ps.project_id=%s and ragapp.has_project_permission(kb.project_id,%s,'knowledge','view') "
                "and kb.deleted_at is null",
                (project_id, user_id),
            ).fetchone()
        return self._model(row) if row else None

    @staticmethod
    def _model(row) -> KnowledgeBase:
        return KnowledgeBase(
            id=row["id"],
            project_id=row["project_id"],
            created_by=row["created_by"],
            name=row["name"],
            created_at=row["created_at"],
        )
