import asyncio
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from modules.chats.models.chat_model import Chat, ChatStatus
from modules.chats.services.chat_service import ChatService
from modules.knowledge_bots.models.models import KnowledgeBot
from modules.projects.models.project_model import Project, ProjectAccess, ProjectRole


class Conversations:
    def __init__(self) -> None:
        self.created: list[Chat] = []
        self.deleted: list = []

    async def create_for_assistant(self, assistant_id, project_id, created_by, title):
        conversation = Chat(
            id=uuid4(),
            assistant_id=assistant_id,
            project_id=project_id,
            created_by=created_by,
            title=title,
            status=ChatStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.created.append(conversation)
        return conversation

    async def list_for_assistant(self, assistant_id, user_id):
        return [chat for chat in self.created if chat.assistant_id == assistant_id]

    async def get(self, chat_id, user_id):
        return next((chat for chat in self.created if chat.id == chat_id), None)

    async def delete(self, chat_id):
        self.deleted.append(chat_id)


class Bots:
    def __init__(self, bot, role=ProjectRole.VIEWER) -> None:
        self.bot = bot
        self.role = role

    async def get(self, bot_id, user_id):
        return self.bot, self.role


class Projects:
    def __init__(self, bot, role) -> None:
        self.bot = bot
        self.role = role

    async def get(self, project_id, user_id):
        return ProjectAccess(
            Project(
                id=project_id,
                workspace_id=uuid4(),
                owner_id=self.bot.created_by,
                name="Workspace",
                description=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            self.role,
        )

    async def require_permission(self, project_id, user_id, feature, action="view"):
        return await self.get(project_id, user_id)


class Unused:
    pass


def service(repository, bot, role=ProjectRole.VIEWER):
    return ChatService(
        repository, Projects(bot, role), Unused(), Unused(), Unused(), Bots(bot, role)
    )


class ConversationServiceTests(unittest.TestCase):
    def test_member_creates_multiple_conversations_for_one_bot(self):
        bot = KnowledgeBot(project_id=uuid4(), created_by=uuid4(), name="Support")
        repository = Conversations()
        conversations = service(repository, bot)
        user_id = uuid4()

        first, role = asyncio.run(
            conversations.create_for_assistant(bot.id, user_id, "First question")
        )
        second, _ = asyncio.run(
            conversations.create_for_assistant(bot.id, user_id, "Second question")
        )

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.assistant_id, bot.id)
        self.assertEqual(second.assistant_id, bot.id)
        self.assertEqual(first.project_id, bot.project_id)
        self.assertIs(role, ProjectRole.VIEWER)

    def test_bot_conversation_list_excludes_other_bots(self):
        bot = KnowledgeBot(project_id=uuid4(), created_by=uuid4(), name="Support")
        other_bot = KnowledgeBot(
            project_id=bot.project_id,
            created_by=bot.created_by,
            name="Finance",
        )
        repository = Conversations()
        conversations = service(repository, bot)
        user_id = uuid4()

        asyncio.run(
            repository.create_for_assistant(bot.id, bot.project_id, user_id, "Included")
        )
        asyncio.run(
            repository.create_for_assistant(
                other_bot.id, bot.project_id, user_id, "Excluded"
            )
        )
        listed, _ = asyncio.run(conversations.list_for_assistant(bot.id, user_id))

        self.assertEqual([chat.title for chat in listed], ["Included"])

    def test_deleting_conversation_only_targets_conversation(self):
        bot = KnowledgeBot(project_id=uuid4(), created_by=uuid4(), name="Support")
        repository = Conversations()
        conversations = service(repository, bot, ProjectRole.EDITOR)
        user_id = uuid4()
        chat, _ = asyncio.run(
            conversations.create_for_assistant(bot.id, user_id, "Temporary")
        )

        asyncio.run(conversations.delete(chat.id, user_id))

        self.assertEqual(repository.deleted, [chat.id])
        self.assertEqual(bot.status.value, "active")
