from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from modules.chats.contracts.chat_generator_contract import ChatGenerator
from modules.chats.contracts.chat_repo_contract import ChatRepositoryContract
from modules.chats.contracts.keysearch_contract import KnowledgeSearch
from modules.chats.contracts.message_contract import MessageRepository
from modules.chats.contracts.project_access_contract import ProjectAccessContract
from modules.chats.models.citation_model import Citation
from modules.chats.models.chat_model import Chat, ChatStatus
from modules.chats.models.error_model import (
    ChatGenerationError,
    ChatNotFoundError,
    ChatPermissionError,
)
from modules.chats.models.message_model import Message, MessageRole
from modules.projects.models.project_model import ProjectRole


class ChatService:
    def __init__(
        self,
        repository: ChatRepositoryContract,
        projects: ProjectAccessContract,
        messages: MessageRepository,
        search: KnowledgeSearch,
        generator: ChatGenerator,
    ) -> None:
        self.repository = repository
        self.projects = projects
        self.messages = messages
        self.search = search
        self.generator = generator

    async def create(self, project_id: UUID, user_id: UUID, title: str) -> tuple[Chat, ProjectRole]:
        access = await self.projects.get(project_id, user_id)
        self._require_editor(access.role)
        chat = await self.repository.create(project_id, user_id, title.strip())
        return chat, access.role

    async def list(self, project_id: UUID, user_id: UUID) -> tuple[list[Chat], ProjectRole]:
        access = await self.projects.get(project_id, user_id)
        chats = await self.repository.list_for_project(project_id, user_id)
        return chats, access.role

    async def get(self, chat_id: UUID, user_id: UUID) -> tuple[Chat, ProjectRole]:
        chat = await self.repository.get(chat_id, user_id)
        if not chat:
            raise ChatNotFoundError
        access = await self.projects.get(chat.project_id, user_id)
        return chat, access.role

    async def update(
        self,
        chat_id: UUID,
        user_id: UUID,
        title: str | None,
        chat_status: ChatStatus | None,
    ) -> tuple[Chat, ProjectRole]:
        chat, role = await self.get(chat_id, user_id)
        self._require_editor(role)
        updated_chat = await self.repository.update(
            chat.id, title.strip() if title else None, chat_status
        )
        return updated_chat, role

    async def delete(self, chat_id: UUID, user_id: UUID) -> None:
        chat, role = await self.get(chat_id, user_id)
        self._require_editor(role)
        await self.repository.delete(chat.id)

    async def list_messages(self, chat_id: UUID, user_id: UUID) -> list[Message]:
        await self.get(chat_id, user_id)
        return await self.messages.list_for_chat(chat_id)

    async def send_message(self, chat_id: UUID, user_id: UUID, content: str) -> Message:
        chat, question, history, chunks, context = await self._prepare_message(
            chat_id, user_id, content
        )
        try:
            answer = await self.generator.generate(
                question,
                context,
                [(message.role.value, message.content) for message in history[-10:]],
            )
        except Exception as error:
            raise ChatGenerationError(str(error)) from error

        assistant = Message(
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=self._citations(chunks),
        )
        await self.messages.add(assistant)
        return assistant

    async def stream_message(
        self, chat_id: UUID, user_id: UUID, content: str
    ) -> AsyncIterator[dict]:
        chat, question, history, chunks, context = await self._prepare_message(
            chat_id, user_id, content
        )
        parts: list[str] = []
        try:
            async for token in self.generator.generate_stream(
                question,
                context,
                [(message.role.value, message.content) for message in history[-10:]],
            ):
                parts.append(token)
                yield {"type": "token", "content": token}
        except Exception as error:
            raise ChatGenerationError(str(error)) from error

        assistant = Message(
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="".join(parts).strip(),
            citations=self._citations(chunks),
        )
        await self.messages.add(assistant)
        yield {"type": "done", "message": assistant}

    async def _prepare_message(self, chat_id: UUID, user_id: UUID, content: str):
        chat, _ = await self.get(chat_id, user_id)
        question = content.strip()
        history = await self.messages.list_for_chat(chat_id)
        
        user_message = Message(chat_id=chat_id, role=MessageRole.USER, content=question)
        await self.messages.add(user_message)

        chunks = await self.search.search(chat.knowledge_base_id, question)
        context = "\n\n".join(
            f"[{index}] Source: {chunk.source_filename}"
            + (f", page {chunk.page_number}" if chunk.page_number else "")
            + f"\n{chunk.text}"
            for index, chunk in enumerate(chunks, 1)
        )
        return chat, question, history, chunks, context or "No relevant passages were found."

    @staticmethod
    def _citations(chunks) -> tuple[Citation, ...]:
        return tuple(
            Citation(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                source_filename=chunk.source_filename,
                excerpt=chunk.text[:600],
                page_number=chunk.page_number,
                element_ids=chunk.element_ids,
                coordinates=chunk.coordinates,
            )
            for chunk in chunks
        )

    @staticmethod
    def _require_editor(role: ProjectRole) -> None:
        if role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise ChatPermissionError