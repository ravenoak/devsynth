"""
Test the integration between WSDE and EDRR, particularly the phase-specific
role assignment functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


class TestWSDEEDRRIntegration:
    """Test the integration between WSDE and EDRR components.

    ReqID: N/A"""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents with different expertise."""
        agents = []
        agent1 = MagicMock()
        agent1.expertise = ["brainstorming", "creativity", "exploration"]
        agent1.current_role = None
        agent1.has_been_primus = False
        agents.append(agent1)
        agent2 = MagicMock()
        agent2.expertise = ["analysis", "evaluation", "critical thinking"]
        agent2.current_role = None
        agent2.has_been_primus = False
        agents.append(agent2)
        agent3 = MagicMock()
        agent3.expertise = ["implementation", "coding", "testing"]
        agent3.current_role = None
        agent3.has_been_primus = False
        agents.append(agent3)
        agent4 = MagicMock()
        agent4.expertise = ["documentation", "reflection", "learning"]
        agent4.current_role = None
        agent4.has_been_primus = False
        agents.append(agent4)
        agent5 = MagicMock()
        agent5.expertise = ["management", "coordination", "planning"]
        agent5.current_role = None
        agent5.has_been_primus = False
        agents.append(agent5)
        return agents

    @pytest.fixture
    def wsde_team(self, mock_agents):
        """Create a WSDE team with mock agents."""
        team = WSDETeam(name="TestEDRRIntegrationTeam", agents=mock_agents)
        return team

    def test_phase_specific_role_assignment_has_expected(self, wsde_team, mock_agents):
        """Test that roles are assigned appropriately for each EDRR phase.

        ReqID: N/A"""
        task = {"type": "code_generation", "language": "python"}
        wsde_team.assign_roles_for_phase(Phase.EXPAND, task)
        print("\nEXPAND phase roles:")
        for agent in mock_agents:
            print(
                f"Agent with expertise {agent.expertise}: role = {agent.current_role}"
            )
        creative_agents = [
            agent
            for agent in mock_agents
            if any(
                exp in ["creativity", "brainstorming", "exploration"]
                for exp in getattr(agent, "expertise", [])
            )
        ]
        assert any(
            agent.current_role in ["Primus", "Designer"] for agent in creative_agents
        ), "No agent with creative expertise was assigned Primus or Designer role in EXPAND phase"
        wsde_team.assign_roles_for_phase(Phase.DIFFERENTIATE, task)
        print("\nDIFFERENTIATE phase roles:")
        for agent in mock_agents:
            print(
                f"Agent with expertise {agent.expertise}: role = {agent.current_role}"
            )
        analytical_agents = [
            agent
            for agent in mock_agents
            if any(
                exp in ["analysis", "evaluation", "critical thinking"]
                for exp in getattr(agent, "expertise", [])
            )
        ]
        assert any(
            agent.current_role in ["Primus", "Evaluator", "Supervisor"]
            for agent in analytical_agents
        ), "No agent with analytical expertise was assigned an appropriate role in DIFFERENTIATE phase"
        wsde_team.assign_roles_for_phase(Phase.REFINE, task)
        print("\nREFINE phase roles:")
        for agent in mock_agents:
            print(
                f"Agent with expertise {agent.expertise}: role = {agent.current_role}"
            )
        implementation_agents = [
            agent
            for agent in mock_agents
            if any(
                exp in ["implementation", "coding", "testing"]
                for exp in getattr(agent, "expertise", [])
            )
        ]
        assert any(
            agent.current_role is not None and agent.current_role != ""
            for agent in implementation_agents
        ), "No agent with implementation expertise was assigned any role in REFINE phase"
        wsde_team.assign_roles_for_phase(Phase.RETROSPECT, task)
        print("\nRETROSPECT phase roles:")
        for agent in mock_agents:
            print(
                f"Agent with expertise {agent.expertise}: role = {agent.current_role}"
            )
        reflective_agents = [
            agent
            for agent in mock_agents
            if any(
                exp in ["reflection", "documentation", "learning"]
                for exp in getattr(agent, "expertise", [])
            )
        ]
        assert any(
            agent.current_role in ["Primus", "Evaluator"] for agent in reflective_agents
        ), "No agent with reflective expertise was assigned Primus or Evaluator role in RETROSPECT phase"

    def test_role_rotation_on_phase_transition_has_expected(
        self, wsde_team, mock_agents
    ):
        """Test that roles are rotated when transitioning between phases.

        ReqID: N/A"""
        task = {"type": "code_generation", "language": "python"}
        wsde_team.assign_roles_for_phase(Phase.EXPAND, task)
        initial_roles = {agent: agent.current_role for agent in mock_agents}
        wsde_team.assign_roles_for_phase(Phase.DIFFERENTIATE, task)
        roles_changed = False
        for agent in mock_agents:
            if agent.current_role != initial_roles[agent]:
                roles_changed = True
                break
        assert roles_changed, "Roles should change during phase transition"

    def test_phase_specific_expertise_scoring_succeeds(self, wsde_team, mock_agents):
        """Test that phase-specific expertise scoring works correctly.

        ReqID: N/A"""
        task = {"type": "code_generation", "language": "python"}
        expand_keywords = [
            "brainstorming",
            "exploration",
            "creativity",
            "ideation",
            "divergent thinking",
            "research",
            "analysis",
            "requirements",
        ]
        score1 = wsde_team._calculate_phase_expertise_score(
            mock_agents[0], task, expand_keywords
        )
        score3 = wsde_team._calculate_phase_expertise_score(
            mock_agents[2], task, expand_keywords
        )
        assert (
            score1 > score3
        ), "Agent with creativity expertise should score higher in EXPAND phase"
        refine_keywords = [
            "implementation",
            "coding",
            "development",
            "optimization",
            "detail-oriented",
            "testing",
            "debugging",
            "quality",
        ]
        score3_refine = wsde_team._calculate_phase_expertise_score(
            mock_agents[2], task, refine_keywords
        )
        score1_refine = wsde_team._calculate_phase_expertise_score(
            mock_agents[0], task, refine_keywords
        )
        assert (
            score3_refine > score1_refine
        ), "Agent with implementation expertise should score higher in REFINE phase"

    def test_dynamic_role_reassignment_and_consensus(self, mock_agents):
        """Dynamic role reassignment integrates with consensus voting."""
        from devsynth.application.collaboration.WSDE import WSDE

        team = WSDE(name="ConsensusTeam", agents=mock_agents)
        task = {
            "phase": "differentiate",
            "description": "choose approach",
            "options": ["a", "b"],
        }
        team.reassign_roles(task)
        assert team.roles["primus"] is not None
        vote = team.run_consensus(task)
        assert vote.get("status") == "completed"
        assert vote.get("decision") or vote.get("result")

    def test_dialectical_hooks_invoked(self, mock_agents):
        """Registered dialectical hooks should be called during reasoning."""
        from devsynth.application.collaboration.WSDE import WSDE

        team = WSDE(name="HookTeam", agents=mock_agents)
        hook = MagicMock()
        team.register_dialectical_hook(hook)
        task = {
            "id": "t1",
            "solutions": [{"content": "sol"}],
        }
        critic = MagicMock()
        team.apply_enhanced_dialectical_reasoning_multi(task, critic)
        hook.assert_called()
