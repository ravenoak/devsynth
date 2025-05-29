import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDE, WSDETeam
from devsynth.domain.models.agent import AgentType, AgentConfig
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.adapters.agents.agent_adapter import SimplifiedAgentFactory, WSDETeamCoordinator, AgentAdapter

class TestAgentCollaboration:
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MagicMock(spec=UnifiedAgent)
        agent.name = "MockAgent"
        agent.agent_type = AgentType.ORCHESTRATOR.value
        agent.current_role = None
        agent.process.return_value = {"result": "Success"}
        return agent

    @pytest.fixture
    def coordinator(self, mock_agent):
        """Create an agent coordinator with a mock agent."""
        coordinator = WSDETeamCoordinator()
        coordinator.create_team("test_team")
        coordinator.add_agent(mock_agent)
        return coordinator

    def test_coordinator_initialization(self):
        """Test that the coordinator initializes correctly."""
        coordinator = WSDETeamCoordinator()
        assert coordinator.teams == {}
        assert coordinator.current_team_id is None

    def test_add_agent(self, mock_agent):
        """Test adding an agent to the coordinator."""
        coordinator = WSDETeamCoordinator()
        # For MVP, the coordinator should create a default team if none exists
        coordinator.add_agent(mock_agent)

        assert len(coordinator.teams["default_team"].agents) == 1
        assert coordinator.teams["default_team"].agents[0] == mock_agent

    def test_delegate_task(self, coordinator, mock_agent):
        """Test delegating a task to the agent."""
        task = {
            "task_type": "specification",
            "requirements": "Build a calculator app"
        }

        result = coordinator.delegate_task(task)
        assert result["result"] == "Success"

        # The agent should have been called with the task
        mock_agent.process.assert_called_once_with(task)

    def test_simplified_agent_factory(self):
        """Test the simplified agent factory."""
        factory = SimplifiedAgentFactory()

        # For MVP, the factory should always return a UnifiedAgent
        agent = factory.create_agent(AgentType.SPECIFICATION.value)
        assert isinstance(agent, UnifiedAgent)

        # Even if we request a different agent type, we should get a UnifiedAgent
        agent = factory.create_agent(AgentType.CODE.value)
        assert isinstance(agent, UnifiedAgent)

    def test_agent_adapter(self, mock_agent):
        """Test the agent adapter."""
        adapter = AgentAdapter()

        # Test creating an agent
        agent = adapter.create_agent(AgentType.ORCHESTRATOR.value)
        assert isinstance(agent, UnifiedAgent)

        # Test creating a team
        team = adapter.create_team("test_team")
        assert team is not None

        # Test adding an agent to the team
        adapter.add_agent_to_team(mock_agent)
        assert len(adapter.agent_coordinator.teams["test_team"].agents) == 1

        # Test processing a task
        task = {"task_type": "specification"}
        mock_agent.process.return_value = {"result": "Specification generated"}

        result = adapter.process_task(task)
        assert result["result"] == "Specification generated"

    def test_backward_compatibility(self):
        """Test backward compatibility with existing code."""
        factory = SimplifiedAgentFactory()

        # Test that we can still create agents with the old agent types
        agent = factory.create_agent(AgentType.SPECIFICATION.value)
        assert isinstance(agent, UnifiedAgent)

        agent = factory.create_agent(AgentType.TEST.value)
        assert isinstance(agent, UnifiedAgent)

        agent = factory.create_agent(AgentType.CODE.value)
        assert isinstance(agent, UnifiedAgent)
