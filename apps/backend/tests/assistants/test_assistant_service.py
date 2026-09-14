import asyncio
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from modules.assistants.models.assistant_model import Assistant
from modules.assistants.services.assistant_service import AssistantService
from modules.projects.models.project_model import ProjectRole


class AssistantServiceTests(unittest.TestCase):
    def test_delete_authorizes_and_deletes_the_loaded_assistant(self):
        user_id = uuid4()
        assistant = Assistant(
            project_id=uuid4(),
            created_by=user_id,
            name="Documentation assistant",
        )
        repository = AsyncMock()
        repository.get.return_value = assistant
        projects = AsyncMock()
        projects.require_permission.return_value.role = ProjectRole.OWNER
        service = AssistantService(repository, projects)

        asyncio.run(service.delete(assistant.id, user_id))

        repository.delete.assert_awaited_once_with(assistant.id)
        projects.require_permission.assert_any_await(
            assistant.project_id, user_id, "assistants", "manage"
        )


if __name__ == "__main__":
    unittest.main()
