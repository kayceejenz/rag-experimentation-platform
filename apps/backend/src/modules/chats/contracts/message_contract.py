from typing import Protocol
from uuid import UUID

from modules.chats.models.message_model import Message


class MessageRepository(Protocol):
    def add(self, message: Message) -> None: ...
    def list_for_conversation(self, conversation_id: UUID) -> list[Message]: ...

