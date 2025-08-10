"""
Unit tests for the dialectical reasoning system.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from devsynth.adapters.requirements.console_notification import (
    ConsoleNotificationAdapter,
)
from devsynth.adapters.requirements.memory_repository import (
    InMemoryChangeRepository,
    InMemoryChatRepository,
    InMemoryDialecticalReasoningRepository,
    InMemoryImpactAssessmentRepository,
    InMemoryRequirementRepository,
)
from devsynth.application.requirements.dialectical_reasoner import (
    ConsensusError,
    DialecticalReasonerService,
)
from devsynth.domain.models.requirement import (
    ChangeType,
    ChatMessage,
    ChatSession,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


class TestDialecticalReasoner(unittest.TestCase):
    """Test cases for the dialectical reasoner.

    ReqID: N/A"""

    def setUp(self):
        """Set up test fixtures."""
        self.requirement_repository = InMemoryRequirementRepository()
        self.change_repository = InMemoryChangeRepository()
        self.reasoning_repository = InMemoryDialecticalReasoningRepository()
        self.impact_repository = InMemoryImpactAssessmentRepository()
        self.chat_repository = InMemoryChatRepository()
        self.notification_service = MagicMock(spec=ConsoleNotificationAdapter)
        self.llm_service = MagicMock()
        self.llm_service.query = MagicMock(return_value="Mock LLM response")
        self.memory_manager = MagicMock()
        self.reasoner = DialecticalReasonerService(
            requirement_repository=self.requirement_repository,
            reasoning_repository=self.reasoning_repository,
            impact_repository=self.impact_repository,
            chat_repository=self.chat_repository,
            notification_service=self.notification_service,
            llm_service=self.llm_service,
            memory_manager=self.memory_manager,
        )
        self.requirement = Requirement(
            id=uuid4(),
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
        )
        self.requirement_repository.save_requirement(self.requirement)
        self.change = RequirementChange(
            id=uuid4(),
            requirement_id=self.requirement.id,
            change_type=ChangeType.MODIFY,
            previous_state=self.requirement,
            new_state=Requirement(
                id=self.requirement.id,
                title="Updated Test Requirement",
                description="This is an updated test requirement",
                status=RequirementStatus.PROPOSED,
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                created_by="test_user",
            ),
            created_by="test_user",
            reason="Testing purposes",
        )
        self.change_repository.save_change(self.change)

    def test_evaluate_change_succeeds(self):
        """Test evaluating a change using dialectical reasoning.

        ReqID: N/A"""
        self.llm_service.query.side_effect = [
            "This is a thesis",
            "This is an antithesis",
            """Argument 1:
Position: Thesis
Content: Argument for thesis

Argument 2:
Position: Antithesis
Content: Argument for antithesis""",
            "This is a synthesis",
            """Conclusion: This is a conclusion

Recommendation: This is a recommendation""",
            "yes",
        ]
        with patch(
            "devsynth.application.requirements.dialectical_reasoner.logger"
        ) as mock_logger:
            reasoning = self.reasoner.evaluate_change(self.change)
            mock_logger.info.assert_any_call(
                "Consensus reached for change",
                extra={"change_id": str(self.change.id), "event": "consensus_reached"},
            )
        self.memory_manager.store_with_edrr_phase.assert_called_once()
        kwargs = self.memory_manager.store_with_edrr_phase.call_args.kwargs
        self.assertEqual(kwargs["edrr_phase"], "REFINE")
        self.assertEqual(reasoning.change_id, self.change.id)
        self.assertEqual(reasoning.thesis, "This is a thesis")
        self.assertEqual(reasoning.antithesis, "This is an antithesis")
        self.assertEqual(reasoning.synthesis, "This is a synthesis")
        self.assertEqual(reasoning.conclusion, "This is a conclusion")
        self.assertEqual(reasoning.recommendation, "This is a recommendation")
        self.assertEqual(len(reasoning.arguments), 2)
        self.assertEqual(reasoning.arguments[0]["position"], "Thesis")
        self.assertEqual(reasoning.arguments[0]["content"], "Argument for thesis")
        self.assertEqual(reasoning.arguments[1]["position"], "Antithesis")
        self.assertEqual(reasoning.arguments[1]["content"], "Argument for antithesis")
        saved_reasoning = self.reasoning_repository.get_reasoning(reasoning.id)
        self.assertIsNotNone(saved_reasoning)
        self.assertEqual(saved_reasoning.id, reasoning.id)
        reasoning_by_change = self.reasoning_repository.get_reasoning_for_change(
            self.change.id
        )
        self.assertIsNotNone(reasoning_by_change)
        self.assertEqual(reasoning_by_change.id, reasoning.id)

    def test_evaluate_change_consensus_failure(self):
        """Ensure consensus failure triggers logging and memory storage."""
        self.llm_service.query.side_effect = [
            "This is a thesis",
            "This is an antithesis",
            """Argument 1:
Position: Thesis
Content: Argument for thesis

Argument 2:
Position: Antithesis
Content: Argument for antithesis""",
            "This is a synthesis",
            """Conclusion: This is a conclusion

Recommendation: This is a recommendation""",
            "no",
        ]
        with patch(
            "devsynth.application.requirements.dialectical_reasoner.logger"
        ) as mock_logger:
            with self.assertRaises(ConsensusError):
                self.reasoner.evaluate_change(self.change)
            mock_logger.error.assert_any_call(
                "Consensus not reached for change",
                extra={"change_id": str(self.change.id), "event": "consensus_failed"},
            )
        self.memory_manager.store_with_edrr_phase.assert_called_once()
        kwargs = self.memory_manager.store_with_edrr_phase.call_args.kwargs
        self.assertEqual(kwargs["edrr_phase"], "RETROSPECT")

    def test_assess_impact_succeeds(self):
        """Test assessing the impact of a change.

        ReqID: N/A"""
        self.llm_service.query.side_effect = [
            "This is an impact analysis",
            """- Recommendation 1
- Recommendation 2
- Recommendation 3""",
        ]
        dependent_requirement = Requirement(
            id=uuid4(),
            title="Dependent Requirement",
            description="This requirement depends on the test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
            dependencies=[self.requirement.id],
        )
        self.requirement_repository.save_requirement(dependent_requirement)
        impact = self.reasoner.assess_impact(self.change)
        self.assertEqual(impact.change_id, self.change.id)
        self.assertEqual(impact.analysis, "This is an impact analysis")
        self.assertEqual(len(impact.recommendations), 3)
        self.assertEqual(impact.recommendations[0], "Recommendation 1")
        self.assertEqual(impact.recommendations[1], "Recommendation 2")
        self.assertEqual(impact.recommendations[2], "Recommendation 3")
        self.assertEqual(len(impact.affected_requirements), 2)
        self.assertIn(self.requirement.id, impact.affected_requirements)
        self.assertIn(dependent_requirement.id, impact.affected_requirements)
        saved_impact = self.impact_repository.get_impact_assessment(impact.id)
        self.assertIsNotNone(saved_impact)
        self.assertEqual(saved_impact.id, impact.id)
        impact_by_change = self.impact_repository.get_impact_assessment_for_change(
            self.change.id
        )
        self.assertIsNotNone(impact_by_change)
        self.assertEqual(impact_by_change.id, impact.id)
        self.notification_service.notify_impact_assessment_completed.assert_called_once_with(
            impact
        )

    def test_create_session_succeeds(self):
        """Test creating a chat session.

        ReqID: N/A"""
        self.llm_service.query.return_value = (
            "Welcome to the dialectical reasoning system!"
        )
        session = self.reasoner.create_session("test_user")
        self.assertEqual(session.user_id, "test_user")
        self.assertIsNone(session.change_id)
        self.assertEqual(session.status, "active")
        self.assertEqual(len(session.messages), 1)
        self.assertEqual(session.messages[0].sender, "system")
        saved_session = self.chat_repository.get_session(session.id)
        self.assertIsNotNone(saved_session)
        self.assertEqual(saved_session.id, session.id)
        reasoning = DialecticalReasoning(
            id=uuid4(),
            change_id=self.change.id,
            thesis="Test thesis",
            antithesis="Test antithesis",
            synthesis="Test synthesis",
            conclusion="Test conclusion",
            recommendation="Test recommendation",
            created_by="test_user",
        )
        self.reasoning_repository.save_reasoning(reasoning)
        self.llm_service.query.return_value = "Welcome to the dialectical reasoning system! We are discussing a change to the requirement."
        session_with_change = self.reasoner.create_session("test_user", self.change.id)
        self.assertEqual(session_with_change.user_id, "test_user")
        self.assertEqual(session_with_change.change_id, self.change.id)
        self.assertEqual(session_with_change.reasoning_id, reasoning.id)
        self.assertEqual(session_with_change.status, "active")
        self.assertEqual(len(session_with_change.messages), 1)
        self.assertEqual(session_with_change.messages[0].sender, "system")

    def test_process_message_succeeds(self):
        """Test processing a message in a chat session.

        ReqID: N/A"""
        session = self.reasoner.create_session("test_user")
        self.llm_service.query.return_value = "This is a response to your message."
        response = self.reasoner.process_message(
            session.id, "Hello, this is a test message.", "test_user"
        )
        self.assertEqual(response.sender, "system")
        self.assertEqual(response.content, "This is a response to your message.")
        self.assertEqual(len(session.messages), 3)
        messages = self.chat_repository.get_messages_for_session(session.id)
        self.assertGreaterEqual(len(messages), 1)
        updated_session = self.chat_repository.get_session(session.id)
        self.assertEqual(len(updated_session.messages), 3)
        self.assertEqual(updated_session.messages[1].sender, "test_user")
        self.assertEqual(
            updated_session.messages[1].content, "Hello, this is a test message."
        )
        self.assertEqual(updated_session.messages[2].sender, "system")
        self.assertEqual(
            updated_session.messages[2].content, "This is a response to your message."
        )


if __name__ == "__main__":
    unittest.main()
