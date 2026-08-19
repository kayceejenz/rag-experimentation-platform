from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Json
from modules.chats.models.citation_model import Citation
from modules.chats.models.message_model import Message, MessageRole


class MessageRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def add(self, message: Message) -> None:
        async with await AsyncConnection.connect(self.database_url) as db:
            await db.execute(
                "insert into ragapp.messages(id,chat_id,role,content,completed_at) "
                "values(%s,%s,%s,%s,now())",
                (message.id, message.chat_id, message.role.value, message.content),
            )
            async with db.cursor() as cursor:
                await cursor.executemany(
                    "insert into ragapp.message_citations(message_id,chunk_id,source_id,"
                    "citation_order,source_filename,excerpt,page_from,page_to,element_ids,coordinates) "
                    "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",
                    [
                        (
                            message.id,
                            citation.chunk_id,
                            citation.source_id,
                            order,
                            citation.source_filename,
                            citation.excerpt,
                            citation.page_number,
                            citation.page_number,
                            list(citation.element_ids),
                            Json(list(citation.coordinates)),
                        )
                        for order, citation in enumerate(message.citations)
                    ],
                )

    async def list_for_chat(self, chat_id) -> list[Message]:
        async with await AsyncConnection.connect(self.database_url, row_factory=dict_row) as db:
            msg_cur = await db.execute(
                "select * from ragapp.messages where chat_id=%s and status='completed' "
                "order by created_at,id",
                (chat_id,),
            )
            rows = await msg_cur.fetchall()
            cita_cur = await db.execute(
                "select mc.* from ragapp.message_citations mc join ragapp.messages m "
                "on m.id=mc.message_id where m.chat_id=%s order by mc.citation_order",
                (chat_id,),
            )
            citations = await cita_cur.fetchall()
        by_message = {}
        for row in citations:
            by_message.setdefault(row["message_id"], []).append(
                Citation(
                    chunk_id=row["chunk_id"],
                    source_id=row["source_id"],
                    source_filename=row["source_filename"],
                    excerpt=row["excerpt"],
                    page_number=row["page_from"],
                    element_ids=tuple(row["element_ids"] or []),
                    coordinates=tuple(row["coordinates"] or []),
                )
            )
        return [
            Message(
                id=row["id"],
                chat_id=row["chat_id"],
                role=MessageRole(row["role"]),
                content=row["content"],
                citations=tuple(by_message.get(row["id"], [])),
                created_at=row["created_at"],
            )
            for row in rows
        ]
