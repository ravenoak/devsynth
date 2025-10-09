"""
End-to-end integration test for WSDE-EDRR integration.

This test verifies the complete integration between the WSDE agent model and the EDRR framework,
including dynamic role assignment, multi-agent collaboration, and dialectical reasoning.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.collaboration.WSDE import WSDE
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.methodology.base import Phase


class ExpertAgent(UnifiedAgent):
    """Agent with specific expertise for testing."""

    def __init__(self, name, expertise):
        super().__init__()
        self.name = name
        self.expertise = expertise
        self.current_role = None
        self.previous_role = None
        self.has_been_primus = False
        config = AgentConfig(
            name=name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(expertise)}",
            capabilities=[],
            parameters={"expertise": expertise},
        )
        self.initialize(config)

    def process(self, task):
        """Process a task based on agent's expertise."""
        return {
            "result": f"Solution from {self.name}",
            "confidence": 0.9,
            "reasoning": f"Based on my expertise in {', '.join(self.expertise)}",
        }


@pytest.fixture
def coordinator():
    """Create an EnhancedEDRRCoordinator with a team of agents with different expertise."""
    team = WSDE(name="TestWsdeEdrrIntegrationEndToEndTeam")
    team.add_agents(
        [
            ExpertAgent(
                "expand_agent",
                ["brainstorming", "exploration", "creativity", "ideation"],
            ),
            ExpertAgent(
                "diff_agent",
                ["comparison", "analysis", "evaluation", "critical thinking"],
            ),
            ExpertAgent(
                "refine_agent",
                ["implementation", "coding", "development", "optimization"],
            ),
            ExpertAgent(
                "retro_agent", ["evaluation", "reflection", "learning", "improvement"]
            ),
        ]
    )
    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.return_value = []
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    mm.store_with_edrr_phase.return_value = "memory_id"
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    return EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        config={
            "edrr": {
                "quality_based_transitions": True,
                "phase_transition": {"auto": True},
            }
        },
    )


@pytest.mark.slow
def test_wsde_edrr_integration_end_to_end_succeeds(coordinator):
    """Test the complete integration between WSDE and EDRR.

    ReqID: N/A"""

    task = {
        "description": "Create a Python function to calculate Fibonacci numbers",
        "language": "python",
        "domain": "code_generation",
    }
    coordinator.start_cycle(task)
    assert coordinator.current_phase == Phase.EXPAND
    primus = coordinator.wsde_team.get_primus()
    assert primus is not None
    role_map = coordinator.wsde_team.get_role_assignments()
    assert role_map
    assert "exploration" in primus.expertise or "brainstorming" in primus.expertise
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)
        assert coordinator.current_phase == phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        if phase == Phase.DIFFERENTIATE:
            assert any(
                skill in ["comparison", "analysis", "evaluation"]
                for skill in primus.expertise
            )
        elif phase == Phase.REFINE:
            assert any(
                skill in ["implementation", "coding", "development"]
                for skill in primus.expertise
            )
        elif phase == Phase.RETROSPECT:
            assert any(
                skill in ["evaluation", "reflection", "learning"]
                for skill in primus.expertise
            )
        results = coordinator.execute_current_phase()
        assert results is not None
    report = coordinator.generate_report()
    assert report is not None
    assert "cycle_id" in report
    assert "phases" in report


@pytest.mark.slow
def test_multi_agent_collaboration_with_memory_succeeds(coordinator):
    """Test multi-agent collaboration with memory system.

    ReqID: N/A"""
    task = {
        "description": "Design a user authentication system",
        "components": ["design", "security", "database"],
        "domain": "system_design",
    }
    coordinator.start_cycle(task)
    original_build_consensus = coordinator.wsde_team._team.build_consensus
    coordinator.wsde_team._team.build_consensus = MagicMock(
        return_value={
            "consensus": "Consensus solution for user authentication",
            "contributors": [agent.name for agent in coordinator.wsde_team.agents],
            "method": "consensus_synthesis",
            "reasoning": "Combined expertise from all agents",
        }
    )
    expand_results = coordinator.execute_current_phase()
    assert expand_results is not None
    coordinator.wsde_team._team.build_consensus = original_build_consensus
    coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    coordinator.memory_manager.retrieve_with_edrr_phase.assert_called()


@pytest.mark.slow
def test_dialectical_reasoning_in_full_workflow_succeeds(coordinator):
    """Test dialectical reasoning in a full workflow.

    ReqID: N/A"""
    task = {
        "description": "Implement a secure password hashing function",
        "language": "python",
        "domain": "security",
    }
    coordinator.start_cycle(task)
    original_dialectical = (
        coordinator.wsde_team._team.apply_enhanced_dialectical_reasoning
    )
    coordinator.wsde_team._team.apply_enhanced_dialectical_reasoning = MagicMock(
        return_value={
            "thesis": {"content": "Initial solution for password hashing"},
            "antithesis": {
                "critique": ["Not using a salt", "Using MD5 which is insecure"],
                "severity": "high",
            },
            "synthesis": {
                "content": "Improved solution using bcrypt with salt",
                "is_improvement": True,
                "addressed_critiques": ["Added salt", "Using bcrypt instead of MD5"],
            },
        }
    )
    coordinator.progress_to_phase(Phase.REFINE)
    refine_results = coordinator.execute_current_phase()
    if "dialectical_reasoning" in refine_results:
        dialectical = refine_results["dialectical_reasoning"]
        assert "thesis" in dialectical
        assert "antithesis" in dialectical
        assert "synthesis" in dialectical
    coordinator.wsde_team._team.apply_enhanced_dialectical_reasoning = (
        original_dialectical
    )


@pytest.mark.slow
def test_peer_review_integration_in_edrr_workflow_succeeds(coordinator):
    """Test the integration of peer review in the EDRR workflow.

    ReqID: N/A"""
    # Configure the coordinator to enable peer review
    coordinator.enable_peer_review = True
    coordinator.peer_review_phases = ["DIFFERENTIATE", "REFINE", "RETROSPECT"]
    coordinator.max_revision_cycles = 1

    # Mock the run_peer_review function and capture flush calls
    with patch.object(coordinator.memory_manager, "flush_updates") as mock_flush:

        def fake_run_peer_review(*args, **kwargs):
            mm = kwargs.get("memory_manager")
            if mm:
                mm.flush_updates()
            return {
                "status": "approved",
                "quality_score": 0.85,
                "feedback": ["Good implementation", "Well-structured code"],
                "all_criteria_passed": True,
                "review_id": "test-review-123",
            }

        with patch(
            "devsynth.application.collaboration.peer_review.run_peer_review",
            side_effect=fake_run_peer_review,
        ) as mock_run_peer_review:
            task = {
                "description": "Create a Python function to calculate factorial",
                "language": "python",
                "domain": "code_generation",
            }
            coordinator.start_cycle(task)

            coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            differentiate_results = coordinator.execute_current_phase()

            assert "peer_review" in differentiate_results
            assert differentiate_results["peer_review"]["status"] == "approved"
            assert differentiate_results["peer_review"]["quality_score"] == 0.85

            coordinator.progress_to_phase(Phase.REFINE)
            refine_results = coordinator.execute_current_phase()
            assert "peer_review" in refine_results
            assert refine_results["peer_review"]["status"] == "approved"

            coordinator.progress_to_phase(Phase.RETROSPECT)
            retrospect_results = coordinator.execute_current_phase()
            assert "peer_review" in retrospect_results
            assert retrospect_results["peer_review"]["status"] == "approved"

            assert mock_run_peer_review.call_count == 3
            for call in mock_run_peer_review.call_args_list:
                assert call.kwargs["memory_manager"] is coordinator.memory_manager

            _, kwargs = mock_run_peer_review.call_args_list[0]
            assert kwargs["work_product"]["phase"] == "DIFFERENTIATE"
            assert "results" in kwargs["work_product"]
            assert kwargs["max_revision_cycles"] == 1

            report = coordinator.generate_report()
            assert "phases" in report
            assert "DIFFERENTIATE" in report["phases"]
            assert "peer_review" in report["phases"]["DIFFERENTIATE"]
            assert "REFINE" in report["phases"]
            assert "peer_review" in report["phases"]["REFINE"]
            assert "RETROSPECT" in report["phases"]
            assert "peer_review" in report["phases"]["RETROSPECT"]

            mock_flush.assert_called()


@pytest.mark.slow
def test_retrospective_phase_synchronizes_memory(coordinator):
    """Ensure retrospective phase flushes memory updates."""

    with patch.object(coordinator.memory_manager, "flush_updates") as mock_flush:
        task = {
            "description": "Sum two numbers",
            "language": "python",
            "domain": "math",
        }
        coordinator.start_cycle(task)
        for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            coordinator.progress_to_phase(phase)
            coordinator.execute_current_phase()

        mock_flush.assert_called()


@pytest.mark.slow
def test_memory_sync_hook_captures_events_during_team_sync():
    """Ensure memory synchronization hooks capture memory updates."""

    mm = MemoryManager()
    events: list[str | None] = []
    mm.register_sync_hook(lambda item: events.append(getattr(item, "id", None)))

    item = MemoryItem(
        id="end-item",
        content={},
        memory_type=MemoryType.TEAM_STATE,
        metadata={},
    )
    mm.update_item("tinydb" if "tinydb" in mm.adapters else "default", item)
    mm.flush_updates()

    assert events == ["end-item", None]
