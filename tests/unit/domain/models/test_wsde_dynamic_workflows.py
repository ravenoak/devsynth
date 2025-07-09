import pytest
from unittest.mock import MagicMock
from devsynth.domain.models.wsde import WSDETeam


class TestWSDERoleReassignment:
    """Tests for the WSDERoleReassignment component.

ReqID: N/A"""

    def setup_method(self):
        self.team = WSDETeam(name='test_dynamic_workflows_team')
        self.doc_agent = MagicMock()
        self.doc_agent.name = 'doc'
        self.doc_agent.expertise = ['documentation', 'markdown']
        self.code_agent = MagicMock()
        self.code_agent.name = 'code'
        self.code_agent.expertise = ['python']
        self.test_agent = MagicMock()
        self.test_agent.name = 'test'
        self.test_agent.expertise = ['testing']
        self.team.add_agents([self.code_agent, self.doc_agent, self.test_agent]
            )

    def test_dynamic_role_reassignment_selects_expert_primus_succeeds(self):
        """Test that dynamic role reassignment selects expert primus succeeds.

ReqID: N/A"""
        task = {'type': 'documentation', 'description': 'Write docs'}
        self.team.dynamic_role_reassignment(task)
        assert self.team.get_primus() == self.doc_agent
        assert self.doc_agent.current_role == 'Primus'

    def test_build_consensus_multiple_solutions_succeeds(self):
        """Test that build consensus multiple solutions succeeds.

ReqID: N/A"""
        task = {'id': 't1', 'description': 'demo'}
        self.team.add_solution(task, {'agent': 'code', 'content': 'a'})
        self.team.add_solution(task, {'agent': 'test', 'content': 'b'})
        consensus = self.team.build_consensus(task)
        assert consensus['consensus'] != ''
        assert set(consensus['contributors']) == {'code', 'test'}
