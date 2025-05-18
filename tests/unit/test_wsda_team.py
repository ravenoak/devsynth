
import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDATeam
from devsynth.application.agents.base import BaseAgent

class TestWSDATeam:
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MagicMock(spec=BaseAgent)
        agent.name = "MockAgent"
        agent.agent_type = "mock"
        agent.current_role = None
        return agent
    
    def test_wsda_team_initialization(self):
        """Test that a WSDATeam initializes correctly."""
        team = WSDATeam()
        assert team.agents == []
        assert team.primus_index == 0
    
    def test_add_agent(self, mock_agent):
        """Test adding an agent to the team."""
        team = WSDATeam()
        team.add_agent(mock_agent)
        assert len(team.agents) == 1
        assert team.agents[0] == mock_agent
    
    def test_rotate_primus(self, mock_agent):
        """Test rotating the Primus role."""
        team = WSDATeam()
        
        # Add multiple agents
        agent1 = mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        
        # Initially, primus_index should be 0
        assert team.primus_index == 0
        
        # After rotation, it should be 1
        team.rotate_primus()
        assert team.primus_index == 1
        
        # After another rotation, it should be 2
        team.rotate_primus()
        assert team.primus_index == 2
        
        # After another rotation, it should wrap back to 0
        team.rotate_primus()
        assert team.primus_index == 0
    
    def test_get_primus(self, mock_agent):
        """Test getting the current Primus agent."""
        team = WSDATeam()
        
        # With no agents, get_primus should return None
        assert team.get_primus() is None
        
        # Add an agent and check that it's the Primus
        team.add_agent(mock_agent)
        assert team.get_primus() == mock_agent
        
        # Add another agent and rotate Primus
        agent2 = MagicMock(spec=BaseAgent)
        team.add_agent(agent2)
        team.rotate_primus()
        assert team.get_primus() == agent2
    
    def test_assign_roles(self, mock_agent):
        """Test assigning WSDE roles to agents."""
        team = WSDATeam()
        
        # Add multiple agents
        agent1 = mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        agent4 = MagicMock(spec=BaseAgent)
        agent5 = MagicMock(spec=BaseAgent)
        
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)
        team.add_agent(agent5)
        
        # Assign roles
        team.assign_roles()
        
        # Check that roles are assigned correctly
        assert agent1.current_role == "Primus"
        
        # Other agents should have Worker, Supervisor, Designer, or Evaluator roles
        assigned_roles = [agent2.current_role, agent3.current_role, agent4.current_role, agent5.current_role]
        assert "Worker" in assigned_roles
        assert "Supervisor" in assigned_roles
        assert "Designer" in assigned_roles
        assert "Evaluator" in assigned_roles
    
    def test_get_role_specific_agents(self, mock_agent):
        """Test getting agents by their specific roles."""
        team = WSDATeam()
        
        # Add multiple agents
        agent1 = MagicMock(spec=BaseAgent)
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        agent4 = MagicMock(spec=BaseAgent)
        agent5 = MagicMock(spec=BaseAgent)
        
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)
        team.add_agent(agent5)
        
        # Manually assign roles for testing
        agent1.current_role = "Primus"
        agent2.current_role = "Worker"
        agent3.current_role = "Supervisor"
        agent4.current_role = "Designer"
        agent5.current_role = "Evaluator"
        
        # Test getting agents by role
        assert team.get_worker() == agent2
        assert team.get_supervisor() == agent3
        assert team.get_designer() == agent4
        assert team.get_evaluator() == agent5
