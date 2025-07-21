"""
Unit Tests for WSDE Voting Mechanisms

This file contains unit tests for the voting mechanisms in the WSDE model,
specifically testing the vote_on_critical_decision method in the WSDETeam class.
"""
import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.agents.unified_agent import UnifiedAgent


class TestWSDEVotingMechanisms:
    """Test suite for the WSDE voting mechanisms.

ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name='test_voting_mechanisms_team')
        self.agent1 = MagicMock()
        self.agent1.name = 'agent1'
        self.agent1.config = MagicMock()
        self.agent1.config.name = 'agent1'
        self.agent1.config.parameters = {'expertise': ['python', 'design']}
        self.agent2 = MagicMock()
        self.agent2.name = 'agent2'
        self.agent2.config = MagicMock()
        self.agent2.config.name = 'agent2'
        self.agent2.config.parameters = {'expertise': ['javascript', 'testing']
            }
        self.agent3 = MagicMock()
        self.agent3.name = 'agent3'
        self.agent3.config = MagicMock()
        self.agent3.config.name = 'agent3'
        self.agent3.config.parameters = {'expertise': ['documentation',
            'planning']}
        self.agent4 = MagicMock()
        self.agent4.name = 'agent4'
        self.agent4.config = MagicMock()
        self.agent4.config.name = 'agent4'
        self.agent4.config.parameters = {'expertise': ['architecture',
            'security']}
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.critical_task = {'type': 'critical_decision', 'description':
            'Choose the best architecture for the system', 'options': [{
            'id': 'option1', 'name': 'Microservices', 'description':
            'Use a microservices architecture'}, {'id': 'option2', 'name':
            'Monolith', 'description': 'Use a monolithic architecture'}, {
            'id': 'option3', 'name': 'Serverless', 'description':
            'Use a serverless architecture'}], 'is_critical': True}
        self.domain_task = {'type': 'critical_decision', 'domain':
            'security', 'description':
            'Choose the authentication method for the system', 'options': [
            {'id': 'option1', 'name': 'OAuth', 'description':
            'Use OAuth for authentication'}, {'id': 'option2', 'name':
            'JWT', 'description': 'Use JWT for authentication'}, {'id':
            'option3', 'name': 'Basic Auth', 'description':
            'Use Basic Auth for authentication'}], 'is_critical': True}

    def test_vote_on_critical_decision_initiates_voting_succeeds(self):
        """Test that vote_on_critical_decision initiates a voting process.

ReqID: N/A"""
        self.agent1.process = MagicMock(return_value={'vote': 'option1'})
        self.agent2.process = MagicMock(return_value={'vote': 'option2'})
        self.agent3.process = MagicMock(return_value={'vote': 'option3'})
        self.agent4.process = MagicMock(return_value={'vote': 'option1'})
        result = self.team.vote_on_critical_decision(self.critical_task)
        assert 'voting_initiated' in result
        assert result['voting_initiated'] is True
        self.agent1.process.assert_called_once()
        self.agent2.process.assert_called_once()
        self.agent3.process.assert_called_once()
        self.agent4.process.assert_called_once()
        assert 'votes' in result
        assert len(result['votes']) == 4
        assert result['votes']['agent1'] == 'option1'
        assert result['votes']['agent2'] == 'option2'
        assert result['votes']['agent3'] == 'option3'
        assert result['votes']['agent4'] == 'option1'

    def test_vote_on_critical_decision_majority_vote_succeeds(self):
        """Test that vote_on_critical_decision uses majority vote to make decisions.

ReqID: N/A"""
        self.agent1.process = MagicMock(return_value={'vote': 'option1'})
        self.agent2.process = MagicMock(return_value={'vote': 'option2'})
        self.agent3.process = MagicMock(return_value={'vote': 'option1'})
        self.agent4.process = MagicMock(return_value={'vote': 'option3'})
        result = self.team.vote_on_critical_decision(self.critical_task)
        assert 'result' in result
        assert result['result'] is not None
        assert 'winner' in result['result']
        assert result['result']['winner'] == 'option1'
        assert 'vote_counts' in result['result']
        assert result['result']['vote_counts']['option1'] == 2
        assert result['result']['vote_counts']['option2'] == 1
        assert result['result']['vote_counts']['option3'] == 1
        assert 'method' in result['result']
        assert result['result']['method'] == 'majority_vote'

    def test_vote_on_critical_decision_tied_vote_succeeds(self):
        """Test that vote_on_critical_decision handles tied votes correctly.

ReqID: N/A"""
        self.agent1.process = MagicMock(return_value={'vote': 'option1'})
        self.agent2.process = MagicMock(return_value={'vote': 'option2'})
        self.agent3.process = MagicMock(return_value={'vote': 'option1'})
        self.agent4.process = MagicMock(return_value={'vote': 'option2'})
        self.team.build_consensus = MagicMock(return_value={'consensus':
            'Use a hybrid architecture combining microservices and monolith',
            'contributors': ['agent1', 'agent2', 'agent3', 'agent4'],
            'method': 'consensus_synthesis', 'reasoning':
            'Combined the best elements from both options'})
        result = self.team.vote_on_critical_decision(self.critical_task)
        assert 'result' in result
        assert 'tied' in result['result']
        assert result['result']['tied'] is True
        assert 'tied_options' in result['result']
        assert 'option1' in result['result']['tied_options']
        assert 'option2' in result['result']['tied_options']
        assert 'vote_counts' in result['result']
        assert result['result']['vote_counts']['option1'] == 2
        assert result['result']['vote_counts']['option2'] == 2
        assert 'method' in result['result']
        assert result['result']['method'] == 'tied_vote'
        assert 'fallback' in result['result']
        assert result['result']['fallback'] == 'primus_tiebreaker'
        assert 'tie_breaking_attempts' in result['result']
        assert len(result['result']['tie_breaking_attempts']) > 0
        assert result['result']['tie_breaking_attempts'][0]['method'
            ] == 'primus_tiebreaker'

    def test_vote_on_critical_decision_weighted_vote_succeeds(self):
        """Test that vote_on_critical_decision uses weighted voting for domain-specific decisions.

ReqID: N/A"""
        self.agent1.config.parameters = {'expertise': ['security',
            'encryption', 'authentication'], 'expertise_level': 'expert'}
        self.agent2.config.parameters = {'expertise': ['security',
            'firewalls'], 'expertise_level': 'intermediate'}
        self.agent3.config.parameters = {'expertise': ['security'],
            'expertise_level': 'novice'}
        self.agent4.config.parameters = {'expertise': ['python',
            'javascript'], 'expertise_level': 'intermediate'}
        self.agent1.process = MagicMock(return_value={'vote': 'option2'})
        self.agent2.process = MagicMock(return_value={'vote': 'option1'})
        self.agent3.process = MagicMock(return_value={'vote': 'option1'})
        self.agent4.process = MagicMock(return_value={'vote': 'option3'})
        result = self.team.vote_on_critical_decision(self.domain_task)
        assert 'result' in result
        assert result['result'] is not None
        if 'winner' in result['result']:
            assert result['result']['winner'] == 'option2'
        elif 'tied' in result['result'] and result['result']['tied']:
            assert 'tie_breaking_attempts' in result['result']
            assert len(result['result']['tie_breaking_attempts']) > 0
            assert result['result']['tie_breaking_attempts'][0]['winner'
                ] == 'option2'
        assert 'votes' in result
        assert result['votes']['agent1'] == 'option2'
        assert result['votes']['agent2'] == 'option1'
        assert result['votes']['agent3'] == 'option1'
        assert result['votes']['agent4'] == 'option3'

    def test_vote_on_critical_decision_records_results_succeeds(self):
        """Test that vote_on_critical_decision records the voting results.

ReqID: N/A"""
        self.agent1.process = MagicMock(return_value={'vote': 'option1'})
        self.agent2.process = MagicMock(return_value={'vote': 'option2'})
        self.agent3.process = MagicMock(return_value={'vote': 'option1'})
        self.agent4.process = MagicMock(return_value={'vote': 'option1'})
        result = self.team.vote_on_critical_decision(self.critical_task)
        assert 'voting_initiated' in result
        assert 'votes' in result
        assert 'result' in result
        assert 'winner' in result['result']
        assert 'vote_counts' in result['result']
        assert 'method' in result['result']
        assert result['result']['vote_counts']['option1'] == 3
        assert result['result']['vote_counts']['option2'] == 1
        assert 'winning_option' in result['result']
        assert result['result']['winning_option']['id'] == 'option1'
        assert result['result']['winning_option']['name'] == 'Microservices'

    def test_vote_on_critical_decision_updates_history_succeeds(self):
        """Ensure voting history is recorded after a vote.

ReqID: N/A"""
        self.agent1.process = MagicMock(return_value={'vote': 'option1'})
        self.agent2.process = MagicMock(return_value={'vote': 'option2'})
        self.agent3.process = MagicMock(return_value={'vote': 'option1'})
        self.agent4.process = MagicMock(return_value={'vote': 'option1'})
        result = self.team.vote_on_critical_decision(self.critical_task)
        assert len(self.team.voting_history) == 1
        entry = self.team.voting_history[0]
        assert entry['task_id'] == self.team._get_task_id(self.critical_task)
        assert entry['result'] == result['result']
