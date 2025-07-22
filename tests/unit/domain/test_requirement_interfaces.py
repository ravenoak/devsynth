import unittest
from uuid import uuid4

from devsynth.domain.interfaces.requirement import (
    InMemoryRequirementRepository,
    InMemoryChangeRepository,
    InMemoryImpactAssessmentRepository,
    InMemoryDialecticalReasoningRepository,
    InMemoryChatRepository,
    SimpleDialecticalReasoner,
    PrintNotificationService,
)
from devsynth.domain.models.requirement import Requirement, RequirementChange


class TestRequirementInterfaces(unittest.TestCase):
    """Tests for concrete implementations of requirement interfaces."""

    def test_inmemory_requirement_repository_crud(self) -> None:
        repo = InMemoryRequirementRepository()
        req = Requirement(title="test")
        repo.save_requirement(req)
        self.assertEqual(repo.get_requirement(req.id), req)
        self.assertEqual(len(repo.get_all_requirements()), 1)
        self.assertTrue(repo.delete_requirement(req.id))
        self.assertIsNone(repo.get_requirement(req.id))

    def test_inmemory_change_repository(self) -> None:
        repo = InMemoryChangeRepository()
        change = RequirementChange(requirement_id=uuid4())
        repo.save_change(change)
        self.assertEqual(repo.get_change(change.id), change)
        self.assertEqual(
            len(repo.get_changes_for_requirement(change.requirement_id)), 1
        )

    def test_dialectical_reasoner_creates_session_and_message(self) -> None:
        chat_repo = InMemoryChatRepository()
        reasoner = SimpleDialecticalReasoner(chat_repo)
        session = reasoner.create_session("user")
        response = reasoner.process_message(session.id, "hello", "user")
        self.assertEqual(response.content, "hello")
        self.assertEqual(len(chat_repo.get_messages_for_session(session.id)), 2)


if __name__ == "__main__":
    unittest.main()
