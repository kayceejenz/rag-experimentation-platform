from typing import Iterator, Protocol
from uuid import UUID

from modules.chats.models.message_model import Message


class MessageRepository(Protocol):
    def add(self, message: Message) -> None: ...
    def list_for_chat(self, chat_id: UUID) -> list[Message]: ...


class ChatGenerator(Protocol):
    def generate(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> str: ...

    def generate_stream(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> Iterator[str]: ...
