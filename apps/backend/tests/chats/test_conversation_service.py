import asyncio
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from modules.chats.models.chat_model import Chat, ChatStatus
from modules.chats.models.retrieval_model import RetrievedChunk
from modules.chats.services.chat_service import ChatService
from modules.assistants.models.assistant_model import Assistant
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


class Assistants:
    def __init__(self, assistant, role=ProjectRole.VIEWER) -> None:
        self.assistant = assistant
        self.role = role

    async def get(self, assistant_id, user_id):
        return self.assistant, self.role


class Projects:
    def __init__(self, assistant, role) -> None:
        self.assistant = assistant
        self.role = role

    async def get(self, project_id, user_id):
        return ProjectAccess(
            Project(
                id=project_id,
                workspace_id=uuid4(),
                owner_id=self.assistant.created_by,
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


def service(repository, assistant, role=ProjectRole.VIEWER):
    return ChatService(
        repository, Projects(assistant, role), Unused(), Unused(), Unused(), Assistants(assistant, role)
    )


class ConversationServiceTests(unittest.TestCase):
    def test_member_creates_multiple_conversations_for_one_assistant(self):
        assistant = Assistant(project_id=uuid4(), created_by=uuid4(), name="Support")
        repository = Conversations()
        conversations = service(repository, assistant)
        user_id = uuid4()

        first, role = asyncio.run(
            conversations.create_for_assistant(assistant.id, user_id, "First question")
        )
        second, _ = asyncio.run(
            conversations.create_for_assistant(assistant.id, user_id, "Second question")
        )

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.assistant_id, assistant.id)
        self.assertEqual(second.assistant_id, assistant.id)
        self.assertEqual(first.project_id, assistant.project_id)
        self.assertIs(role, ProjectRole.VIEWER)

    def test_assistant_conversation_list_excludes_other_assistants(self):
        assistant = Assistant(project_id=uuid4(), created_by=uuid4(), name="Support")
        other_assistant = Assistant(
            project_id=assistant.project_id,
            created_by=assistant.created_by,
            name="Finance",
        )
        repository = Conversations()
        conversations = service(repository, assistant)
        user_id = uuid4()

        asyncio.run(
            repository.create_for_assistant(assistant.id, assistant.project_id, user_id, "Included")
        )
        asyncio.run(
            repository.create_for_assistant(
                other_assistant.id, assistant.project_id, user_id, "Excluded"
            )
        )
        listed, _ = asyncio.run(conversations.list_for_assistant(assistant.id, user_id))

        self.assertEqual([chat.title for chat in listed], ["Included"])

    def test_deleting_conversation_only_targets_conversation(self):
        assistant = Assistant(project_id=uuid4(), created_by=uuid4(), name="Support")
        repository = Conversations()
        conversations = service(repository, assistant, ProjectRole.EDITOR)
        user_id = uuid4()
        chat, _ = asyncio.run(
            conversations.create_for_assistant(assistant.id, user_id, "Temporary")
        )

        asyncio.run(conversations.delete(chat.id, user_id))

        self.assertEqual(repository.deleted, [chat.id])
        self.assertEqual(assistant.status.value, "active")

    def test_only_answered_sources_become_citations(self):
        first = RetrievedChunk(
            chunk_id=uuid4(),
            source_id=uuid4(),
            source_filename="first.pdf",
            text="First passage",
            score=0.9,
            page_number=1,
            element_ids=(),
            coordinates=(),
            metadata={},
        )
        second = RetrievedChunk(
            chunk_id=uuid4(),
            source_id=uuid4(),
            source_filename="second.pdf",
            text="Second passage",
            score=0.8,
            page_number=2,
            element_ids=(),
            coordinates=(),
            metadata={},
        )

        answer, citations = ChatService._grounded_response(
            "The answer comes from the second passage [2].", [first, second]
        )

        self.assertEqual("The answer comes from the second passage [1].", answer)
        self.assertEqual([second.chunk_id], [item.chunk_id for item in citations])

    def test_answer_without_references_has_no_citations_or_empty_marker(self):
        chunk = RetrievedChunk(
            chunk_id=uuid4(),
            source_id=uuid4(),
            source_filename="guide.pdf",
            text="Passage",
            score=0.9,
            page_number=None,
            element_ids=(),
            coordinates=(),
            metadata={},
        )

        answer, citations = ChatService._grounded_response(
            "I do not have enough information. []", [chunk]
        )

        self.assertEqual("I do not have enough information.", answer)
        self.assertEqual((), citations)
