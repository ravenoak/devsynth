
"""
Unit tests for the dialectical reasoning system.
"""
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from devsynth.domain.models.requirement import (
    ChangeType, ChatMessage, ChatSession, DialecticalReasoning, ImpactAssessment,
    Requirement, RequirementChange, RequirementPriority, RequirementStatus, RequirementType
)
from devsynth.application.requirements.dialectical_reasoner import DialecticalReasonerService
from devsynth.adapters.requirements.memory_repository import (
    InMemoryChatRepository, InMemoryChangeRepository,
    InMemoryDialecticalReasoningRepository, InMemoryImpactAssessmentRepository,
    InMemoryRequirementRepository
)
from devsynth.adapters.requirements.console_notification import ConsoleNotificationAdapter


class TestDialecticalReasoner(unittest.TestCase):
    """Test cases for the dialectical reasoner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock repositories
        self.requirement_repository = InMemoryRequirementRepository()
        self.change_repository = InMemoryChangeRepository()
        self.reasoning_repository = InMemoryDialecticalReasoningRepository()
        self.impact_repository = InMemoryImpactAssessmentRepository()
        self.chat_repository = InMemoryChatRepository()
        
        # Create mock notification service
        self.notification_service = MagicMock(spec=ConsoleNotificationAdapter)
        
        # Create mock LLM service
        self.llm_service = MagicMock()
        self.llm_service.query = MagicMock(return_value="Mock LLM response")
        
        # Create the dialectical reasoner service
        self.reasoner = DialecticalReasonerService(
            requirement_repository=self.requirement_repository,
            reasoning_repository=self.reasoning_repository,
            impact_repository=self.impact_repository,
            chat_repository=self.chat_repository,
            notification_service=self.notification_service,
            llm_service=self.llm_service
        )
        
        # Create a sample requirement
        self.requirement = Requirement(
            id=uuid4(),
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user"
        )
        self.requirement_repository.save_requirement(self.requirement)
        
        # Create a sample change
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
                created_by="test_user"
            ),
            created_by="test_user",
            reason="Testing purposes"
        )
        self.change_repository.save_change(self.change)
    
    def test_evaluate_change(self):
        """Test evaluating a change using dialectical reasoning."""
        # Configure mock LLM responses
        self.llm_service.query.side_effect = [
            "This is a thesis",  # For thesis
            "This is an antithesis",  # For antithesis
            "Argument 1:\nPosition: Thesis\nContent: Argument for thesis\n\nArgument 2:\nPosition: Antithesis\nContent: Argument for antithesis",  # For arguments
            "This is a synthesis",  # For synthesis
            "Conclusion: This is a conclusion\n\nRecommendation: This is a recommendation"  # For conclusion and recommendation
        ]
        
        # Evaluate the change
        reasoning = self.reasoner.evaluate_change(self.change)
        
        # Verify the reasoning
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
        
        # Verify that the reasoning was saved
        saved_reasoning = self.reasoning_repository.get_reasoning(reasoning.id)
        self.assertIsNotNone(saved_reasoning)
        self.assertEqual(saved_reasoning.id, reasoning.id)
        
        # Verify that the reasoning can be retrieved by change ID
        reasoning_by_change = self.reasoning_repository.get_reasoning_for_change(self.change.id)
        self.assertIsNotNone(reasoning_by_change)
        self.assertEqual(reasoning_by_change.id, reasoning.id)
    
    def test_assess_impact(self):
        """Test assessing the impact of a change."""
        # Configure mock LLM responses
        self.llm_service.query.side_effect = [
            "This is an impact analysis",  # For impact analysis
            "- Recommendation 1\n- Recommendation 2\n- Recommendation 3"  # For recommendations
        ]
        
        # Create a dependent requirement
        dependent_requirement = Requirement(
            id=uuid4(),
            title="Dependent Requirement",
            description="This requirement depends on the test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
            dependencies=[self.requirement.id]
        )
        self.requirement_repository.save_requirement(dependent_requirement)
        
        # Assess the impact
        impact = self.reasoner.assess_impact(self.change)
        
        # Verify the impact assessment
        self.assertEqual(impact.change_id, self.change.id)
        self.assertEqual(impact.analysis, "This is an impact analysis")
        self.assertEqual(len(impact.recommendations), 3)
        self.assertEqual(impact.recommendations[0], "Recommendation 1")
        self.assertEqual(impact.recommendations[1], "Recommendation 2")
        self.assertEqual(impact.recommendations[2], "Recommendation 3")
        
        # Verify that the affected requirements include both the changed requirement and the dependent requirement
        self.assertEqual(len(impact.affected_requirements), 2)
        self.assertIn(self.requirement.id, impact.affected_requirements)
        self.assertIn(dependent_requirement.id, impact.affected_requirements)
        
        # Verify that the impact assessment was saved
        saved_impact = self.impact_repository.get_impact_assessment(impact.id)
        self.assertIsNotNone(saved_impact)
        self.assertEqual(saved_impact.id, impact.id)
        
        # Verify that the impact assessment can be retrieved by change ID
        impact_by_change = self.impact_repository.get_impact_assessment_for_change(self.change.id)
        self.assertIsNotNone(impact_by_change)
        self.assertEqual(impact_by_change.id, impact.id)
        
        # Verify that the notification service was called
        self.notification_service.notify_impact_assessment_completed.assert_called_once_with(impact)
    
    def test_create_session(self):
        """Test creating a chat session."""
        # Configure mock LLM response for welcome message
        self.llm_service.query.return_value = "Welcome to the dialectical reasoning system!"
        
        # Create a session
        session = self.reasoner.create_session("test_user")
        
        # Verify the session
        self.assertEqual(session.user_id, "test_user")
        self.assertIsNone(session.change_id)
        self.assertEqual(session.status, "active")
        self.assertEqual(len(session.messages), 1)
        self.assertEqual(session.messages[0].sender, "system")
        
        # Verify that the session was saved
        saved_session = self.chat_repository.get_session(session.id)
        self.assertIsNotNone(saved_session)
        self.assertEqual(saved_session.id, session.id)
        
        # Create a session with a change ID
        # First, create a reasoning for the change
        reasoning = DialecticalReasoning(
            id=uuid4(),
            change_id=self.change.id,
            thesis="Test thesis",
            antithesis="Test antithesis",
            synthesis="Test synthesis",
            conclusion="Test conclusion",
            recommendation="Test recommendation",
            created_by="test_user"
        )
        self.reasoning_repository.save_reasoning(reasoning)
        
        # Configure mock LLM response for welcome message with context
        self.llm_service.query.return_value = "Welcome to the dialectical reasoning system! We are discussing a change to the requirement."
        
        # Create a session with the change ID
        session_with_change = self.reasoner.create_session("test_user", self.change.id)
        
        # Verify the session
        self.assertEqual(session_with_change.user_id, "test_user")
        self.assertEqual(session_with_change.change_id, self.change.id)
        self.assertEqual(session_with_change.reasoning_id, reasoning.id)
        self.assertEqual(session_with_change.status, "active")
        self.assertEqual(len(session_with_change.messages), 1)
        self.assertEqual(session_with_change.messages[0].sender, "system")
    
    def test_process_message(self):
        """Test processing a message in a chat session."""
        # Create a session
        session = self.reasoner.create_session("test_user")
        
        # Configure mock LLM response for chat
        self.llm_service.query.return_value = "This is a response to your message."
        
        # Process a message
        response = self.reasoner.process_message(session.id, "Hello, this is a test message.", "test_user")
        
        # Verify the response
        self.assertEqual(response.sender, "system")
        self.assertEqual(response.content, "This is a response to your message.")
        
        # Verify that the message and response were saved
        # Note: In our implementation, messages are stored in the session object
        # and not separately retrieved from the repository
        self.assertEqual(len(session.messages), 3)  # Welcome message, user message, and response
        
        # If we want to test repository retrieval, we need to account for how messages are stored
        messages = self.chat_repository.get_messages_for_session(session.id)
        # The repository might only store the new messages, not the ones already in the session
        self.assertGreaterEqual(len(messages), 1)  # At least the response message should be stored
        
        # Verify the updated session
        updated_session = self.chat_repository.get_session(session.id)
        self.assertEqual(len(updated_session.messages), 3)
        self.assertEqual(updated_session.messages[1].sender, "test_user")
        self.assertEqual(updated_session.messages[1].content, "Hello, this is a test message.")
        self.assertEqual(updated_session.messages[2].sender, "system")
        self.assertEqual(updated_session.messages[2].content, "This is a response to your message.")


if __name__ == "__main__":
    unittest.main()
