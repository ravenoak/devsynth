import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDE, WSDETeam
from devsynth.domain.models.agent import AgentType, AgentConfig
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.adapters.agents.agent_adapter import (
    SimplifiedAgentFactory,
    WSDETeamCoordinator,
    AgentAdapter,
)
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.exceptions import ValidationError


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
        task = {"task_type": "specification", "requirements": "Build a calculator app"}

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

    def test_team_task_phase_notifications(self):
        coordinator = AgentCoordinatorImpl(
            {
                "features": {
                    "wsde_collaboration": True,
                    "collaboration_notifications": True,
                }
            }
        )

        planner = MagicMock(spec=UnifiedAgent)
        planner.name = "planner"
        planner.agent_type = "planner"
        planner.current_role = None
        planner.process.return_value = {"solution": "plan"}

        worker = MagicMock(spec=UnifiedAgent)
        worker.name = "worker"
        worker.agent_type = "code"
        worker.current_role = None
        worker.process.return_value = {"solution": "code"}

        coordinator.add_agent(planner)
        coordinator.add_agent(worker)

        team = coordinator.team
        team.assign_roles_for_phase = MagicMock()
        team.assign_roles = MagicMock()
        team.select_primus_by_expertise = MagicMock()
        team.get_primus = MagicMock(return_value=planner)
        team.broadcast_message = MagicMock()
        team.add_solution = MagicMock()
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "final",
                "contributors": ["planner", "worker"],
                "method": "consensus",
            }
        )

        task = {"team_task": True, "phase": "expand", "description": "demo"}
        result = coordinator.delegate_task(task)

        team.assign_roles_for_phase.assert_called_once()
        phase_arg = team.assign_roles_for_phase.call_args[0][0]
        assert phase_arg.value == "expand"

        team.broadcast_message.assert_any_call(
            "planner",
            "task_assignment",
            subject="Team task started",
            content=task,
            metadata={"phase": "expand"},
        )
        team.broadcast_message.assert_any_call(
            "system",
            "status_update",
            subject="Team task completed",
            content=team.build_consensus.return_value,
            metadata={"phase": "expand"},
        )

        assert result["result"] == "final"

    def test_delegate_task_agent_type_not_found(self):
        coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})

        agent = MagicMock(spec=UnifiedAgent)
        agent.name = "planner"
        agent.agent_type = "planner"
        coordinator.add_agent(agent)

        with pytest.raises(ValidationError):
            coordinator.delegate_task({"agent_type": "nonexistent"})

    def test_delegate_task_multi_agent_consensus(self):
        coordinator = WSDETeamCoordinator()
        coordinator.create_team("team")

        a1 = MagicMock(spec=UnifiedAgent)
        a1.name = "a1"
        a1.config = AgentConfig(
            name="a1",
            agent_type=AgentType.ORCHESTRATOR,
            description="",
            capabilities=[],
            parameters={"expertise": ["code"]},
        )
        a1.process.return_value = {"result": "sol1"}

        a2 = MagicMock(spec=UnifiedAgent)
        a2.name = "a2"
        a2.config = AgentConfig(
            name="a2",
            agent_type=AgentType.ORCHESTRATOR,
            description="",
            capabilities=[],
            parameters={"expertise": ["test"]},
        )
        a2.process.return_value = {"result": "sol2"}

        coordinator.add_agents([a1, a2])
        team = coordinator.get_team("team")
        team.select_primus_by_expertise = MagicMock()
        team.get_primus = MagicMock(return_value=a1)
        team.add_solution = MagicMock()
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "final",
                "contributors": ["a1", "a2"],
                "method": "consensus",
                "reasoning": "",
            }
        )
        team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
            return_value={"evaluation": "ok"}
        )

        result = coordinator.delegate_task({"description": "demo"})

        team.build_consensus.assert_called_once()
        team.apply_enhanced_dialectical_reasoning_multi.assert_called_once_with(
            {"description": "demo"}, a1
        )
        assert result["result"] == "final"
        assert "dialectical_analysis" in result

    def test_delegate_task_dynamic_role_assignment(self):
        coordinator = WSDETeamCoordinator()
        coordinator.create_team("dyn")

        a1 = MagicMock(spec=UnifiedAgent)
        a1.name = "a1"
        a1.config = AgentConfig(
            name="a1",
            agent_type=AgentType.ORCHESTRATOR,
            description="",
            capabilities=[],
            parameters={"expertise": ["code"]},
        )
        a1.process.return_value = {"result": "s1"}

        a2 = MagicMock(spec=UnifiedAgent)
        a2.name = "a2"
        a2.config = AgentConfig(
            name="a2",
            agent_type=AgentType.ORCHESTRATOR,
            description="",
            capabilities=[],
            parameters={"expertise": ["test"]},
        )
        a2.process.return_value = {"result": "s2"}

        coordinator.add_agents([a1, a2])
        team = coordinator.get_team("dyn")
        team.select_primus_by_expertise = MagicMock()
        team.get_primus = MagicMock(return_value=a1)
        team.add_solution = MagicMock()
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "ok",
                "contributors": ["a1", "a2"],
                "method": "consensus",
                "reasoning": "",
            }
        )
        team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
            return_value={"eval": "ok"}
        )

        task = {"description": "demo", "type": "code"}
        result = coordinator.delegate_task(task)

        team.select_primus_by_expertise.assert_called_once_with(task)
        assert result["contributors"] == ["a1", "a2"]

    def test_delegate_task_voting(self):
        coordinator = WSDETeamCoordinator()
        coordinator.create_team("team")

        agent = MagicMock(spec=UnifiedAgent)
        agent.name = "a"
        agent.config = AgentConfig(
            name="a",
            agent_type=AgentType.ORCHESTRATOR,
            description="",
            capabilities=[],
            parameters={},
        )
        coordinator.add_agent(agent)
        coordinator.add_agent(agent)

        team = coordinator.get_team("team")
        team.vote_on_critical_decision = MagicMock(
            return_value={"voting_initiated": True}
        )

        task = {"type": "critical_decision", "is_critical": True}
        result = coordinator.delegate_task(task)
        team.vote_on_critical_decision.assert_called_once_with(task)
        assert result["voting_initiated"]

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

    def test_delegate_calls_select_primus_before_processing(self):
        coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
        a1 = MagicMock(spec=UnifiedAgent)
        a1.name = "a1"
        a1.agent_type = "code"
        a1.current_role = None
        a1.expertise = ["python"]
        a2 = MagicMock(spec=UnifiedAgent)
        a2.name = "a2"
        a2.agent_type = "docs"
        a2.current_role = None
        a2.expertise = ["documentation"]
        coordinator.add_agent(a1)
        coordinator.add_agent(a2)

        team = coordinator.team
        order = []
        original_select = team.select_primus_by_expertise

        def select_spy(task):
            order.append("select")
            return original_select(task)

        with patch.object(
            team, "select_primus_by_expertise", side_effect=select_spy
        ) as spy:

            def process_side_effect(task):
                order.append("process")
                return {"solution": "ok"}

            a1.process.side_effect = process_side_effect
            a2.process.return_value = {"solution": "ok"}
            team.get_primus = MagicMock(return_value=a1)
            team.add_solution = MagicMock()
            team.build_consensus = MagicMock(
                return_value={
                    "consensus": "x",
                    "contributors": ["a1", "a2"],
                    "method": "consensus",
                }
            )

            result = coordinator.delegate_task({"team_task": True, "type": "code"})

        spy.assert_called_once_with({"team_task": True, "type": "code"})
        assert order and order[0] == "select"
        assert result["method"] == "consensus"
