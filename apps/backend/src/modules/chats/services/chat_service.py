from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from modules.chats.contracts.chat_generator_contract import ChatGenerator
from modules.chats.contracts.chat_repo_contract import ChatRepositoryContract
from modules.chats.contracts.keysearch_contract import KnowledgeSearch
from modules.chats.contracts.message_contract import MessageRepository
from modules.chats.contracts.project_access_contract import ProjectAccessContract
from modules.chats.models.chat_model import Chat, ChatStatus
from modules.chats.models.citation_model import Citation
from modules.chats.models.error_model import (
    ChatGenerationError,
    ChatNotFoundError,
    ChatPermissionError,
)
from modules.chats.models.message_model import Message, MessageRole
from modules.knowledge_bots.services.knowledge_bot_service import KnowledgeBotService
from modules.projects.models.project_model import ProjectRole


class ChatService:
    def __init__(
        self,
        repository: ChatRepositoryContract,
        projects: ProjectAccessContract,
        messages: MessageRepository,
        search: KnowledgeSearch,
        generator: ChatGenerator,
        bots: KnowledgeBotService,
        runtime_factory=None,
    ) -> None:
        self.repository = repository
        self.projects = projects
        self.messages = messages
        self.search = search
        self.generator = generator
        self.bots = bots
        self.runtime_factory = runtime_factory

    async def list(
        self, project_id: UUID, user_id: UUID
    ) -> tuple[list[Chat], ProjectRole]:
        access = await self.projects.require_permission(
            project_id, user_id, "assistants"
        )
        chats = await self.repository.list_for_project(project_id, user_id)
        return chats, access.role

    async def create_for_assistant(
        self, assistant_id: UUID, user_id: UUID, title: str
    ) -> tuple[Chat, ProjectRole]:
        bot, role = await self.bots.get(assistant_id, user_id)
        await self.projects.require_permission(bot.project_id, user_id, "assistants")
        chat = await self.repository.create_for_assistant(
            bot.id, bot.project_id, user_id, title.strip()
        )
        return chat, role

    async def list_for_assistant(
        self, assistant_id: UUID, user_id: UUID
    ) -> tuple[list[Chat], ProjectRole]:
        bot, role = await self.bots.get(assistant_id, user_id)
        chats = await self.repository.list_for_assistant(bot.id, user_id)
        return chats, role

    async def get(self, chat_id: UUID, user_id: UUID) -> tuple[Chat, ProjectRole]:
        chat = await self.repository.get(chat_id, user_id)
        if not chat:
            raise ChatNotFoundError
        access = await self.projects.require_permission(
            chat.project_id, user_id, "assistants"
        )
        return chat, access.role

    async def update(
        self,
        chat_id: UUID,
        user_id: UUID,
        title: str | None,
        chat_status: ChatStatus | None,
    ) -> tuple[Chat, ProjectRole]:
        chat, role = await self.get(chat_id, user_id)
        await self.projects.require_permission(
            chat.project_id, user_id, "assistants", "manage"
        )
        updated_chat = await self.repository.update(
            chat.id, title.strip() if title else None, chat_status
        )
        return updated_chat, role

    async def delete(self, chat_id: UUID, user_id: UUID) -> None:
        chat, _ = await self.get(chat_id, user_id)
        await self.projects.require_permission(
            chat.project_id, user_id, "assistants", "manage"
        )
        await self.repository.delete(chat.id)

    async def list_messages(self, chat_id: UUID, user_id: UUID) -> list[Message]:
        await self.get(chat_id, user_id)
        return await self.messages.list_for_conversation(chat_id)

    async def send_message(self, chat_id: UUID, user_id: UUID, content: str) -> Message:
        (
            chat,
            question,
            history,
            chunks,
            context,
            generator,
        ) = await self._prepare_message(chat_id, user_id, content)
        try:
            answer = await generator.generate(
                question,
                context,
                [(message.role.value, message.content) for message in history[-10:]],
            )
        except Exception as error:
            raise ChatGenerationError(str(error)) from error

        assistant = Message(
            conversation_id=chat.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=self._citations(chunks),
        )
        await self.messages.add(assistant)
        return assistant

    async def stream_message(
        self, chat_id: UUID, user_id: UUID, content: str
    ) -> AsyncIterator[dict]:
        yield {
            "type": "tool_step",
            "tool": {
                "id": "kb-search",
                "type": "search",
                "label": "Searching knowledge base",
                "status": "running",
            },
        }

        (
            chat,
            question,
            history,
            chunks,
            context,
            generator,
        ) = await self._prepare_message(chat_id, user_id, content)

        yield {
            "type": "tool_step",
            "tool": {
                "id": "kb-search",
                "type": "search",
                "label": "Searching knowledge base",
                "status": "completed",
            },
        }

        answer_parts: list[str] = []
        thinking_parts: list[str] = []
        try:
            async for part in generator.generate_stream(
                question,
                context,
                [(message.role.value, message.content) for message in history[-10:]],
            ):
                if part["kind"] == "thinking":
                    thinking_parts.append(part["text"])
                    yield {"type": "thinking_delta", "content": part["text"]}
                else:
                    answer_parts.append(part["text"])
                    yield {"type": "token", "content": part["text"]}
        except Exception as error:
            raise ChatGenerationError(str(error)) from error

        assistant = Message(
            conversation_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="".join(answer_parts).strip(),
            citations=self._citations(chunks),
        )
        await self.messages.add(assistant)
        yield {
            "type": "done",
            "message": assistant,
            "reasoning": "".join(thinking_parts).strip() or None,
        }

    async def _prepare_message(self, chat_id: UUID, user_id: UUID, content: str):
        chat, _ = await self.get(chat_id, user_id)
        if not self.runtime_factory:
            raise ChatGenerationError("Assistant runtime is not configured")
        try:
            configuration = await self.bots.runtime_configuration(
                chat.assistant_id, user_id
            )
            search, generator = self.runtime_factory.create(configuration)
            history = await self.messages.list_for_conversation(chat.id)
            question = Message(
                conversation_id=chat.id, role=MessageRole.USER, content=content.strip()
            )
            await self.messages.add(question)
            chunks = await search.search(
                configuration["knowledge_base_id"],
                question.content,
                int(configuration["retrieval"]["top_k"]),
            )
            context = "\n\n".join(
                f"[{index}] {chunk.source_filename}: {chunk.text}"
                for index, chunk in enumerate(chunks, 1)
            )
            return chat, question.content, history, chunks, context, generator
        except Exception as error:
            if isinstance(error, ChatGenerationError):
                raise
            raise ChatGenerationError(str(error)) from error

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
