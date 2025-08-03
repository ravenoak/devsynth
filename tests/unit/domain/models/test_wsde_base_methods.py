import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from devsynth.domain.models.wsde_base import WSDETeam


class TestWSDEBaseMethods:
    """Test suite for methods in wsde_base.py that aren't covered by existing tests.

ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name='test_wsde_team')
        self.agent1 = MagicMock()
        self.agent1.name = 'agent1'
        self.agent1.current_role = None
        self.agent1.parameters = {'expertise': ['python', 'code_generation']}
        self.agent2 = MagicMock()
        self.agent2.name = 'agent2'
        self.agent2.current_role = None
        self.agent2.parameters = {'expertise': ['testing', 'test_generation']}
        self.agent3 = MagicMock()
        self.agent3.name = 'agent3'
        self.agent3.current_role = None
        self.agent3.parameters = {'expertise': ['documentation', 'markdown']}

    def test_add_agents_succeeds(self):
        """Test adding multiple agents at once.

ReqID: N/A"""
        agents = [self.agent1, self.agent2, self.agent3]
        self.team.add_agents(agents)
        assert len(self.team.agents) == 3
        assert self.team.agents[0] == self.agent1
        assert self.team.agents[1] == self.agent2
        assert self.team.agents[2] == self.agent3

    @pytest.mark.medium
    def test_register_dialectical_hook_succeeds(self):
        """Test registering a dialectical hook.

ReqID: N/A"""
        hook_called = False

        def test_hook_succeeds(self, thesis, antitheses):
            """Test that hook succeeds.

ReqID: N/A"""
            nonlocal hook_called
            hook_called = True
            return {'synthesis': 'test synthesis'}
        self.team.register_dialectical_hook(test_hook_succeeds)
        assert len(self.team.dialectical_hooks) > 0
        assert self.team.dialectical_hooks[-1] == test_hook_succeeds
        # Since we can't directly call the hook through the team object,
        # we'll just call it directly to verify it works
        thesis = {'content': 'test thesis'}
        antitheses = [{'content': 'test antithesis'}]
        result = test_hook_succeeds(thesis, antitheses)
        assert hook_called
        assert result == {'synthesis': 'test synthesis'}

    @pytest.mark.medium
    def test_send_message_succeeds(self):
        """Test sending a message between agents.

ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        message = self.team.send_message(sender='agent1', recipients=[
            'agent2', 'agent3'], message_type='test_message', subject=
            'Test Subject', content='Test Content', metadata={'key': 'value'})
        assert message is not None
        assert len(self.team.messages) == 1
        message = self.team.messages[0]
        assert message['sender'] == 'agent1'
        assert message['recipients'] == ['agent2', 'agent3']
        assert message['type'] == 'test_message'
        assert message['subject'] == 'Test Subject'
        assert message['content'] == 'Test Content'
        assert message['metadata'] == {'key': 'value'}
        assert 'timestamp' in message
        assert 'id' in message

    @pytest.mark.medium
    def test_broadcast_message_succeeds(self):
        """Test broadcasting a message to all agents.

ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        message = self.team.broadcast_message(sender='agent1',
            message_type='broadcast_test', subject='Broadcast Subject',
            content='Broadcast Content', metadata={'broadcast': True})
        assert message is not None
        assert len(self.team.messages) == 1
        message = self.team.messages[0]
        assert message['sender'] == 'agent1'
        assert message['recipients'] == ['agent2', 'agent3']
        assert message['type'] == 'broadcast_test'
        assert message['subject'] == 'Broadcast Subject'
        assert message['content'] == 'Broadcast Content'
        assert message['metadata'] == {'broadcast': True}
        assert 'timestamp' in message
        assert 'id' in message

    @pytest.mark.medium
    def test_get_messages_succeeds(self):
        """Test getting messages with filters.

ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.send_message(sender='agent1', recipients=['agent2'],
            message_type='type1', subject='Subject 1', content='Content 1')
        self.team.send_message(sender='agent2', recipients=['agent1',
            'agent3'], message_type='type2', subject='Subject 2', content=
            'Content 2')
        self.team.send_message(sender='agent3', recipients=['agent1'],
            message_type='type1', subject='Subject 3', content='Content 3')
        all_messages = self.team.get_messages()
        assert len(all_messages) == 3
        agent1_messages = self.team.get_messages(agent='agent1')
        assert len(agent1_messages) == 3
        type1_messages = self.team.get_messages(filters={'type': 'type1'})
        assert len(type1_messages) == 2
        assert type1_messages[0]['type'] == 'type1'
        assert type1_messages[1]['type'] == 'type1'

    @pytest.mark.medium
    def test_conduct_peer_review_succeeds(self):
        """Test conducting a peer review.

ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        work_product = {'code':
            "def example():\n    return 'Hello, World!'", 'description':
            'A simple example function'}
        with patch.object(self.team, 'request_peer_review') as mock_request:
            mock_review_request = {
                'id': 'test-id',
                'timestamp': datetime.now(),
                'work_product': work_product,
                'author': self.agent1.name,
                'reviewers': [self.agent2.name, self.agent3.name],
                'status': 'requested',
                'reviews': []
            }
            mock_request.return_value = mock_review_request
            result = self.team.conduct_peer_review(work_product=
                work_product, author=self.agent1, reviewer_agents=[self.
                agent2, self.agent3])
            mock_request.assert_called_once_with(work_product, self.agent1, [self.agent2, self.agent3])
            assert result == mock_review_request
