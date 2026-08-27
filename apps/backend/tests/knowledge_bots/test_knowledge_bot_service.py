import asyncio
import unittest
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from modules.knowledge_bots.models import (
    KnowledgeBot,
    KnowledgeBotNotFoundError,
    KnowledgeBotPermissionError,
    KnowledgeBotStatus,
)
from modules.knowledge_bots.service import KnowledgeBotService
from modules.projects.models.project_model import Project, ProjectAccess, ProjectRole


class BotRepository:
    def __init__(self, bot: KnowledgeBot | None = None) -> None:
        self.bot = bot
        self.deleted = False

    async def create(self, project_id, created_by, name, description):
        self.bot = KnowledgeBot(
            project_id=project_id,
            created_by=created_by,
            name=name,
            description=description,
        )
        return self.bot

    async def get(self, bot_id, user_id):
        return self.bot if self.bot and self.bot.id == bot_id else None

    async def list_for_project(self, project_id, user_id):
        return [self.bot] if self.bot and self.bot.project_id == project_id else []

    async def update(self, bot_id, name, description, update_description, bot_status):
        self.bot = replace(
            self.bot,
            name=name or self.bot.name,
            description=description if update_description else self.bot.description,
            status=bot_status or self.bot.status,
        )
        return self.bot

    async def delete(self, bot_id):
        self.deleted = True


class Projects:
    def __init__(self, role: ProjectRole) -> None:
        self.role = role

    async def get(self, project_id, user_id):
        return ProjectAccess(
            Project(
                id=project_id,
                owner_id=user_id,
                name="Workspace",
                description=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            self.role,
        )


def run(coroutine):
    return asyncio.run(coroutine)


class KnowledgeBotServiceTests(unittest.TestCase):
    def test_editor_can_create_bot_with_normalized_values(self):
        repository = BotRepository()
        service = KnowledgeBotService(repository, Projects(ProjectRole.EDITOR))

        bot, role = run(service.create(uuid4(), uuid4(), "  Support bot  ", "  Docs  "))

        self.assertEqual(bot.name, "Support bot")
        self.assertEqual(bot.description, "Docs")
        self.assertIs(role, ProjectRole.EDITOR)

    def test_viewer_cannot_create_or_update_bot(self):
        bot = KnowledgeBot(project_id=uuid4(), created_by=uuid4(), name="Support")
        repository = BotRepository(bot)
        service = KnowledgeBotService(repository, Projects(ProjectRole.VIEWER))

        with self.assertRaises(KnowledgeBotPermissionError):
            run(service.create(bot.project_id, uuid4(), "Another", None))

        with self.assertRaises(KnowledgeBotPermissionError):
            run(service.update(bot.id, uuid4(), "Changed", None, False, None))

    def test_update_can_clear_description_and_archive_bot(self):
        bot = KnowledgeBot(
            project_id=uuid4(), created_by=uuid4(), name="Support", description="Old"
        )
        repository = BotRepository(bot)
        service = KnowledgeBotService(repository, Projects(ProjectRole.OWNER))

        updated, _ = run(
            service.update(bot.id, uuid4(), None, None, True, KnowledgeBotStatus.ARCHIVED)
        )

        self.assertIsNone(updated.description)
        self.assertIs(updated.status, KnowledgeBotStatus.ARCHIVED)

    def test_missing_bot_is_not_exposed_as_permission_failure(self):
        service = KnowledgeBotService(BotRepository(), Projects(ProjectRole.OWNER))

        with self.assertRaises(KnowledgeBotNotFoundError):
            run(service.get(uuid4(), uuid4()))
