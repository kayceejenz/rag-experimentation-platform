from __future__ import annotations

from uuid import UUID

from modules.chats.contracts.chat_repo_contract import (
    ChatRepositoryContract,
)
from modules.chats.contracts.keysearch_contract import KnowledgeSearch
from modules.chats.contracts.project_access_contract import ProjectAccessContract
from modules.chats.contracts.message_contract import ChatGenerator, MessageRepository
from modules.chats.models.chat_model import (
    Chat,
    ChatStatus,
)
from modules.chats.models.error_model import ChatGenerationError, ChatNotFoundError, ChatPermissionError
from modules.projects.models.project_model import ProjectRole
from modules.chats.models.citation_model import Citation
from modules.chats.models.message_model import Message, MessageRole


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

    def create(self, project_id: UUID, user_id: UUID, title: str) -> tuple[Chat, ProjectRole]:
        access = self.projects.get(project_id, user_id)
        self._require_editor(access.role)
        return self.repository.create(project_id, user_id, title.strip()), access.role

    def list(self, project_id: UUID, user_id: UUID) -> tuple[list[Chat], ProjectRole]:
        access = self.projects.get(project_id, user_id)
        return self.repository.list_for_project(project_id, user_id), access.role

    def get(self, chat_id: UUID, user_id: UUID) -> tuple[Chat, ProjectRole]:
        chat = self.repository.get(chat_id, user_id)
        if not chat:
            raise ChatNotFoundError
        access = self.projects.get(chat.project_id, user_id)
        return chat, access.role

    def update(
        self,
        chat_id: UUID,
        user_id: UUID,
        title: str | None,
        chat_status: ChatStatus | None,
    ) -> tuple[Chat, ProjectRole]:
        chat, role = self.get(chat_id, user_id)
        self._require_editor(role)
        return self.repository.update(chat.id, title.strip() if title else None, chat_status), role

    def delete(self, chat_id: UUID, user_id: UUID) -> None:
        chat, role = self.get(chat_id, user_id)
        self._require_editor(role)
        self.repository.delete(chat.id)

    def list_messages(self, chat_id: UUID, user_id: UUID) -> list[Message]:
        self.get(chat_id, user_id)
        return self.messages.list_for_chat(chat_id)

    def send_message(self, chat_id: UUID, user_id: UUID, content: str) -> Message:
        chat, _ = self.get(chat_id, user_id)
        question = content.strip()
        history = self.messages.list_for_chat(chat_id)
        user_message = Message(chat_id=chat_id, role=MessageRole.USER, content=question)
        self.messages.add(user_message)

        chunks = self.search.search(chat.knowledge_base_id, question)
        context = "\n\n".join(
            f"[{index}] Source: {chunk.source_filename}"
            + (f", page {chunk.page_number}" if chunk.page_number else "")
            + f"\n{chunk.text}"
            for index, chunk in enumerate(chunks, 1)
        )
        try:
            answer = self.generator.generate(
                question,
                context or "No relevant passages were found.",
                [(message.role.value, message.content) for message in history[-10:]],
            )
        except Exception as error:
            raise ChatGenerationError(str(error)) from error
        citations = tuple(
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
        assistant = Message(
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=citations,
        )
        self.messages.add(assistant)
        return assistant

    @staticmethod
    def _require_editor(role: ProjectRole) -> None:
        if role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise ChatPermissionError
