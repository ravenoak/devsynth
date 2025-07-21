"""
Unit tests for the requirement models.
"""
import unittest
from datetime import datetime
from uuid import uuid4
from devsynth.domain.models.requirement import ChangeType, ChatMessage, ChatSession, DialecticalReasoning, ImpactAssessment, Requirement, RequirementChange, RequirementPriority, RequirementStatus, RequirementType


class TestRequirementModels(unittest.TestCase):
    """Test cases for the requirement models.

ReqID: N/A"""

    def test_requirement_model_succeeds(self):
        """Test the Requirement model.

ReqID: N/A"""
        requirement = Requirement(title='Test Requirement', description=
            'This is a test requirement', status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM, type=RequirementType.
            FUNCTIONAL, created_by='test_user', tags=['test', 'requirement'
            ], metadata={'component': 'test_component'})
        self.assertEqual(requirement.title, 'Test Requirement')
        self.assertEqual(requirement.description, 'This is a test requirement')
        self.assertEqual(requirement.status, RequirementStatus.DRAFT)
        self.assertEqual(requirement.priority, RequirementPriority.MEDIUM)
        self.assertEqual(requirement.type, RequirementType.FUNCTIONAL)
        self.assertEqual(requirement.created_by, 'test_user')
        self.assertEqual(requirement.tags, ['test', 'requirement'])
        self.assertEqual(requirement.metadata, {'component': 'test_component'})
        requirement.update(title='Updated Requirement', status=
            RequirementStatus.APPROVED, tags=['updated', 'requirement'])
        self.assertEqual(requirement.title, 'Updated Requirement')
        self.assertEqual(requirement.status, RequirementStatus.APPROVED)
        self.assertEqual(requirement.tags, ['updated', 'requirement'])
        self.assertEqual(requirement.description, 'This is a test requirement')

    def test_requirement_change_model_succeeds(self):
        """Test the RequirementChange model.

ReqID: N/A"""
        requirement = Requirement(title='Test Requirement', description=
            'This is a test requirement', status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM, type=RequirementType.
            FUNCTIONAL, created_by='test_user')
        updated_requirement = Requirement(id=requirement.id, title=
            'Updated Requirement', description=
            'This is an updated test requirement', status=RequirementStatus
            .APPROVED, priority=RequirementPriority.HIGH, type=
            RequirementType.FUNCTIONAL, created_by='test_user')
        change = RequirementChange(requirement_id=requirement.id,
            change_type=ChangeType.MODIFY, previous_state=requirement,
            new_state=updated_requirement, created_by='test_user', reason=
            'Testing purposes')
        self.assertEqual(change.requirement_id, requirement.id)
        self.assertEqual(change.change_type, ChangeType.MODIFY)
        self.assertEqual(change.previous_state, requirement)
        self.assertEqual(change.new_state, updated_requirement)
        self.assertEqual(change.created_by, 'test_user')
        self.assertEqual(change.reason, 'Testing purposes')
        self.assertFalse(change.approved)
        self.assertIsNone(change.approved_at)
        self.assertIsNone(change.approved_by)
        self.assertEqual(change.comments, [])

    def test_impact_assessment_model_succeeds(self):
        """Test the ImpactAssessment model.

ReqID: N/A"""
        impact = ImpactAssessment(change_id=uuid4(), affected_requirements=
            [uuid4(), uuid4()], affected_components=['component1',
            'component2'], risk_level='medium', estimated_effort='high',
            analysis='This is an impact analysis', recommendations=[
            'Recommendation 1', 'Recommendation 2'], created_by='test_user')
        self.assertEqual(impact.risk_level, 'medium')
        self.assertEqual(impact.estimated_effort, 'high')
        self.assertEqual(impact.analysis, 'This is an impact analysis')
        self.assertEqual(impact.recommendations, ['Recommendation 1',
            'Recommendation 2'])
        self.assertEqual(impact.created_by, 'test_user')
        self.assertEqual(len(impact.affected_requirements), 2)
        self.assertEqual(impact.affected_components, ['component1',
            'component2'])

    def test_dialectical_reasoning_model_succeeds(self):
        """Test the DialecticalReasoning model.

ReqID: N/A"""
        reasoning = DialecticalReasoning(change_id=uuid4(), thesis=
            'This is a thesis', antithesis='This is an antithesis',
            arguments=[{'position': 'thesis', 'content':
            'Argument for thesis'}, {'position': 'antithesis', 'content':
            'Argument for antithesis'}], synthesis='This is a synthesis',
            conclusion='This is a conclusion', recommendation=
            'This is a recommendation', created_by='test_user')
        self.assertEqual(reasoning.thesis, 'This is a thesis')
        self.assertEqual(reasoning.antithesis, 'This is an antithesis')
        self.assertEqual(reasoning.synthesis, 'This is a synthesis')
        self.assertEqual(reasoning.conclusion, 'This is a conclusion')
        self.assertEqual(reasoning.recommendation, 'This is a recommendation')
        self.assertEqual(reasoning.created_by, 'test_user')
        self.assertEqual(len(reasoning.arguments), 2)
        self.assertEqual(reasoning.arguments[0]['position'], 'thesis')
        self.assertEqual(reasoning.arguments[0]['content'],
            'Argument for thesis')
        self.assertEqual(reasoning.arguments[1]['position'], 'antithesis')
        self.assertEqual(reasoning.arguments[1]['content'],
            'Argument for antithesis')

    def test_chat_models_succeeds(self):
        """Test the ChatMessage and ChatSession models.

ReqID: N/A"""
        session = ChatSession(user_id='test_user', change_id=uuid4(),
            status='active')
        self.assertEqual(session.user_id, 'test_user')
        self.assertEqual(session.status, 'active')
        self.assertEqual(session.messages, [])
        message1 = session.add_message('test_user',
            'Hello, this is a test message')
        message2 = session.add_message('system', 'This is a response')
        self.assertEqual(message1.sender, 'test_user')
        self.assertEqual(message1.content, 'Hello, this is a test message')
        self.assertEqual(message1.session_id, session.id)
        self.assertEqual(message2.sender, 'system')
        self.assertEqual(message2.content, 'This is a response')
        self.assertEqual(message2.session_id, session.id)
        self.assertEqual(len(session.messages), 2)
        self.assertEqual(session.messages[0], message1)
        self.assertEqual(session.messages[1], message2)


if __name__ == '__main__':
    unittest.main()
