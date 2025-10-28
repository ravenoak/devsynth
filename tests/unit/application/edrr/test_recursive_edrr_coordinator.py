"""Tests for the recursive functionality of the EDRRCoordinator class."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def memory_manager():
    """Create a mock memory manager."""
    mock = MagicMock(spec=MemoryManager)
    mock.stored_items = {}
    mock.store_with_edrr_phase.side_effect = (
        lambda item, item_type, phase, metadata: mock.stored_items.update(
            {item_type: {"item": item, "phase": phase, "metadata": metadata}}
        )
    )
    mock.retrieve_with_edrr_phase.side_effect = (
        lambda item_type, phase, metadata: mock.stored_items.get(item_type, {}).get(
            "item", {}
        )
    )
    mock.retrieve_historical_patterns.return_value = []
    mock.retrieve_relevant_knowledge.return_value = []
    return mock


@pytest.fixture
def wsde_team():
    """Create a mock WSDE team."""
    mock = MagicMock(spec=WSDETeam)
    mock.generate_diverse_ideas.return_value = [
        {"id": 1, "idea": "Test Idea 1"},
        {"id": 2, "idea": "Test Idea 2"},
    ]
    mock.create_comparison_matrix.return_value = {
        "idea_1": {"feasibility": 0.8},
        "idea_2": {"feasibility": 0.6},
    }
    mock.evaluate_options.return_value = [
        {"id": 1, "score": 0.8},
        {"id": 2, "score": 0.6},
    ]
    mock.analyze_trade_offs.return_value = [
        {"id": 1, "trade_offs": ["Trade-off 1", "Trade-off 2"]}
    ]
    mock.formulate_decision_criteria.return_value = {
        "criteria_1": 0.5,
        "criteria_2": 0.5,
    }
    mock.select_best_option.return_value = {"id": 1, "idea": "Test Idea 1"}
    mock.elaborate_details.return_value = [
        {"step": 1, "description": "Step 1"},
        {"step": 2, "description": "Step 2"},
    ]
    mock.create_implementation_plan.return_value = [
        {"task": 1, "description": "Task 1"},
        {"task": 2, "description": "Task 2"},
    ]
    mock.optimize_implementation.return_value = {
        "optimized": True,
        "plan": [{"task": 1}, {"task": 2}],
    }
    mock.perform_quality_assurance.return_value = {
        "issues": [],
        "recommendations": ["Recommendation 1"],
    }
    mock.extract_learnings.return_value = [
        {"category": "Process", "learning": "Learning 1"}
    ]
    mock.recognize_patterns.return_value = [{"pattern": "Pattern 1", "frequency": 0.8}]
    mock.integrate_knowledge.return_value = {"integrated": True, "knowledge_items": 2}
    mock.generate_improvement_suggestions.return_value = [
        {"phase": "EXPAND", "suggestion": "Suggestion 1"}
    ]
    return mock


@pytest.fixture
def code_analyzer():
    """Create a mock code analyzer."""
    mock = MagicMock(spec=CodeAnalyzer)
    mock.analyze_project_structure.return_value = {
        "files": 10,
        "classes": 5,
        "functions": 20,
    }
    return mock


@pytest.fixture
def ast_transformer():
    """Create a mock AST transformer."""
    return MagicMock(spec=AstTransformer)


@pytest.fixture
def prompt_manager():
    """Create a mock prompt manager."""
    return MagicMock(spec=PromptManager)


@pytest.fixture
def documentation_manager():
    """Create a mock documentation manager."""
    return MagicMock(spec=DocumentationManager)


@pytest.fixture
def coordinator(
    memory_manager,
    wsde_team,
    code_analyzer,
    ast_transformer,
    prompt_manager,
    documentation_manager,
):
    """Create an EDRRCoordinator instance."""
    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
    )


class TestRecursiveEDRRCoordinator:
    """Tests for the recursive functionality of the EDRRCoordinator class.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_initialization_with_recursion_support_succeeds(self, coordinator):
        """Test that the coordinator is initialized with recursion support.

        ReqID: N/A"""
        assert hasattr(coordinator, "parent_cycle_id")
        assert hasattr(coordinator, "recursion_depth")
        assert hasattr(coordinator, "child_cycles")
        assert coordinator.parent_cycle_id is None
        assert coordinator.recursion_depth == 0
        assert coordinator.child_cycles == []

    @pytest.mark.medium
    def test_create_micro_cycle_succeeds(self, coordinator):
        """Test creating a micro-EDRR cycle.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        macro_cycle_id = coordinator.cycle_id
        micro_task = {"description": "Micro Task"}
        micro_cycle = coordinator.create_micro_cycle(micro_task, Phase.EXPAND)
        assert micro_cycle is not None
        assert micro_cycle.parent_cycle_id == macro_cycle_id
        assert micro_cycle.recursion_depth == 1
        assert micro_cycle.task == micro_task
        assert micro_cycle in coordinator.child_cycles

    @pytest.mark.medium
    def test_recursion_depth_limit_succeeds(self, coordinator):
        """Test that recursion depth is limited.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        current_cycle = coordinator
        for i in range(1, coordinator.max_recursion_depth + 1):
            micro_task = {"description": f"Micro Task Level {i}"}
            current_cycle = current_cycle.create_micro_cycle(micro_task, Phase.EXPAND)
            assert current_cycle.recursion_depth == i
        with pytest.raises(EDRRCoordinatorError):
            current_cycle.create_micro_cycle({"description": "Too Deep"}, Phase.EXPAND)

    @pytest.mark.medium
    def test_create_micro_cycle_terminated_succeeds(self, coordinator):
        """Test that create micro cycle terminated succeeds.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro"})
        with patch.object(
            coordinator,
            "should_terminate_recursion",
            return_value=(True, "test reason"),
        ):
            with pytest.raises(EDRRCoordinatorError) as excinfo:
                coordinator.create_micro_cycle({"description": "Sub"}, Phase.EXPAND)
            assert "test reason" in str(excinfo.value)
        assert not coordinator.child_cycles

    @pytest.mark.medium
    def test_micro_edrr_within_expand_phase_has_expected(self, coordinator):
        """Test micro-EDRR cycles within the Expand phase.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        original_execute = coordinator._execute_expand_phase

        def mock_execute_expand(context=None):
            coordinator.create_micro_cycle(
                {"description": "Brainstorm Ideas"}, Phase.EXPAND
            )
            coordinator.create_micro_cycle(
                {"description": "Research Existing Solutions"}, Phase.EXPAND
            )
            coordinator.create_micro_cycle(
                {"description": "Analyze Requirements"}, Phase.EXPAND
            )
            return original_execute(context)

        coordinator._execute_expand_phase = mock_execute_expand
        coordinator.execute_current_phase()
        assert len(coordinator.child_cycles) == 3
        assert all(
                cycle.parent_cycle_id == coordinator.cycle_id
                for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    @pytest.mark.medium
    def test_micro_edrr_within_differentiate_phase_has_expected(self, coordinator):
        """Test micro-EDRR cycles within the Differentiate phase.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        original_execute = coordinator._execute_differentiate_phase

        def mock_execute_differentiate(context=None):
            coordinator.create_micro_cycle(
                {"description": "Compare Approaches"}, Phase.DIFFERENTIATE
            )
            coordinator.create_micro_cycle(
                {"description": "Evaluate Trade-offs"}, Phase.DIFFERENTIATE
            )
            coordinator.create_micro_cycle(
                {"description": "Select Best Approach"}, Phase.DIFFERENTIATE
            )
            return original_execute(context)

        coordinator._execute_differentiate_phase = mock_execute_differentiate
        coordinator.execute_current_phase()
        assert len(coordinator.child_cycles) == 3
        assert all(
                cycle.parent_cycle_id == coordinator.cycle_id
                for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    @pytest.mark.medium
    def test_micro_edrr_within_refine_phase_has_expected(self, coordinator):
        """Test micro-EDRR cycles within the Refine phase.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.REFINE)
        original_execute = coordinator._execute_refine_phase

        def mock_execute_refine(context=None):
            coordinator.create_micro_cycle(
                {"description": "Implement Solution"}, Phase.REFINE
            )
            coordinator.create_micro_cycle(
                {"description": "Optimize Performance"}, Phase.REFINE
            )
            coordinator.create_micro_cycle(
                {"description": "Ensure Quality"}, Phase.REFINE
            )
            return original_execute(context)

        coordinator._execute_refine_phase = mock_execute_refine
        coordinator.execute_current_phase()
        assert len(coordinator.child_cycles) == 3
        assert all(
                cycle.parent_cycle_id == coordinator.cycle_id
                for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    @pytest.mark.medium
    def test_micro_edrr_within_retrospect_phase_has_expected(self, coordinator):
        """Test micro-EDRR cycles within the Retrospect phase.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.RETROSPECT)
        original_execute = coordinator._execute_retrospect_phase

        def mock_execute_retrospect(context=None):
            coordinator.create_micro_cycle(
                {"description": "Extract Learnings"}, Phase.RETROSPECT
            )
            coordinator.create_micro_cycle(
                {"description": "Identify Patterns"}, Phase.RETROSPECT
            )
            coordinator.create_micro_cycle(
                {"description": "Generate Improvements"}, Phase.RETROSPECT
            )
            return original_execute(context)

        coordinator._execute_retrospect_phase = mock_execute_retrospect
        coordinator.execute_current_phase()
        assert len(coordinator.child_cycles) == 3
        assert all(
                cycle.parent_cycle_id == coordinator.cycle_id
                for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    @pytest.mark.medium
    def test_granularity_threshold_check_succeeds(self, coordinator):
        """Test granularity threshold check for recursion termination.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        micro_task = {"description": "Very small task", "granularity_score": 0.1}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == True
        assert reason == "granularity threshold"
        micro_task = {"description": "Complex task", "granularity_score": 0.8}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == False
        assert reason is None

    @pytest.mark.medium
    def test_cost_benefit_analysis_succeeds(self, coordinator):
        """Test cost-benefit analysis for recursion termination.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        micro_task = {
            "description": "High cost task",
            "cost_score": 0.9,
            "benefit_score": 0.2,
        }
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == True
        assert reason == "cost-benefit analysis"
        micro_task = {
            "description": "High benefit task",
            "cost_score": 0.3,
            "benefit_score": 0.8,
        }
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == False
        assert reason is None

    @pytest.mark.parametrize(
        "micro_task",
        [
            {"description": "Too granular", "granularity_score": 0.1},
            {"description": "Too costly", "cost_score": 0.9, "benefit_score": 0.2},
        ],
    )
    @pytest.mark.medium
    def test_create_micro_cycle_termination_succeeds(self, coordinator, micro_task):
        """create_micro_cycle should abort when delimiting principles trigger.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate is True
        assert reason is not None
        with pytest.raises(EDRRCoordinatorError):
            coordinator.create_micro_cycle(micro_task, Phase.EXPAND)
        assert not coordinator.child_cycles

    @pytest.mark.medium
    def test_quality_threshold_monitoring_succeeds(self, coordinator):
        """Test quality threshold monitoring for recursion termination.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        micro_task = {"description": "High quality task", "quality_score": 0.95}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == True
        assert reason == "quality threshold"
        micro_task = {"description": "Low quality task", "quality_score": 0.5}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == False
        assert reason is None

    @pytest.mark.medium
    def test_resource_limits_succeeds(self, coordinator):
        """Test resource limits for recursion termination.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        micro_task = {"description": "Resource intensive task", "resource_usage": 0.9}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == True
        assert reason == "resource limit"
        micro_task = {"description": "Lightweight task", "resource_usage": 0.2}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == False
        assert reason is None

    @pytest.mark.medium
    def test_human_judgment_override_succeeds(self, coordinator):
        """Test human judgment override for recursion termination.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        micro_task = {
            "description": "Task with override",
            "human_override": "terminate",
        }
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == True
        assert reason == "human override"
        micro_task = {"description": "Task with override", "human_override": "continue"}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate == False
        assert reason is None
        micro_task = {"description": "Task without override"}
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate in [True, False]
        if should_terminate:
            assert reason is not None
        else:
            assert reason is None

    @pytest.mark.medium
    def test_recursive_execution_tracking_succeeds(self, coordinator):
        """Test tracking of recursive execution.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro Task"})
        macro_cycle_id = coordinator.cycle_id
        micro_cycle = coordinator.create_micro_cycle(
            {"description": "Micro Task"}, Phase.EXPAND
        )
        micro_cycle.execute_current_phase()
        assert f"EXPAND_{micro_cycle.cycle_id}" in micro_cycle._execution_traces
        assert (
            micro_cycle._execution_traces[f"EXPAND_{micro_cycle.cycle_id}"][
                "parent_cycle_id"
            ]
            == macro_cycle_id
        )
        assert (
            micro_cycle._execution_traces[f"EXPAND_{micro_cycle.cycle_id}"][
                "recursion_depth"
            ]
            == 1
        )

    @pytest.mark.medium
    def test_auto_micro_cycle_creation_succeeds(self, coordinator):
        """Test that auto micro cycle creation succeeds.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro"})
        context = {
            "micro_tasks": [
                {"description": "Sub1", "granularity_score": 0.8},
                {"description": "Sub2", "granularity_score": 0.8},
            ]
        }
        results = coordinator._execute_expand_phase(context)
        assert len(coordinator.child_cycles) == 2
        assert len(results["micro_cycle_results"]) == 2

    @pytest.mark.medium
    def test_create_micro_cycle_max_depth_stop_fails(self, coordinator):
        """Ensure micro cycle creation fails when max depth is reached.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "root"})
        current = coordinator
        for i in range(coordinator.max_recursion_depth):
            current = current.create_micro_cycle(
                {"description": f"level {i}"}, Phase.EXPAND
            )
        assert current.recursion_depth == coordinator.max_recursion_depth
        with pytest.raises(EDRRCoordinatorError):
            current.create_micro_cycle({"description": "extra"}, Phase.EXPAND)
        assert not current.child_cycles

    @pytest.mark.medium
    def test_decide_next_phase_phase_complete_has_expected(self, coordinator):
        """_decide_next_phase should transition when phase is complete.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name]["phase_complete"] = True
        next_phase = coordinator._decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    @pytest.mark.medium
    def test_decide_next_phase_timeout_has_expected(self, coordinator):
        """_decide_next_phase should transition after timeout.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name].pop("phase_complete", None)
        coordinator.phase_transition_timeout = 1
        coordinator._phase_start_times[Phase.EXPAND] = datetime.now() - timedelta(
            seconds=2
        )
        next_phase = coordinator._decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    @pytest.mark.medium
    def test_decide_next_phase_no_transition_returns_expected_result(self, coordinator):
        """_decide_next_phase should return None when conditions not met.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name].pop("phase_complete", None)
        coordinator.phase_transition_timeout = 100
        coordinator._phase_start_times[Phase.EXPAND] = datetime.now()
        assert coordinator._decide_next_phase() is None

    @pytest.mark.medium
    def test_should_terminate_recursion_all_factors_true_succeeds(self, coordinator):
        """If all delimiting principles trigger, recursion should terminate.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro"})
        task = {
            "description": "child",
            "human_override": "terminate",
            "granularity_score": 0.1,
            "cost_score": 0.9,
            "benefit_score": 0.2,
            "quality_score": 0.95,
            "resource_usage": 0.9,
        }
        should_terminate, reason = coordinator.should_terminate_recursion(task)
        assert should_terminate is True
        assert reason == "human override"

    @pytest.mark.medium
    def test_should_terminate_recursion_all_factors_false_succeeds(self, coordinator):
        """If no delimiting principle triggers, recursion should continue.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "Macro"})
        task = {
            "description": "child",
            "human_override": "continue",
            "granularity_score": 0.8,
            "cost_score": 0.2,
            "benefit_score": 0.9,
            "quality_score": 0.5,
            "resource_usage": 0.3,
        }
        should_terminate, reason = coordinator.should_terminate_recursion(task)
        assert should_terminate is False
        assert reason is None

    @pytest.mark.medium
    def test_get_performance_metrics_total_duration_succeeds(self, coordinator):
        """get_performance_metrics should report aggregated duration.

        ReqID: N/A"""
        coordinator.performance_metrics = {
            Phase.EXPAND.name: {"duration": 1.0},
            Phase.DIFFERENTIATE.name: {"duration": 2.0},
            Phase.REFINE.name: {"duration": 3.0},
            Phase.RETROSPECT.name: {"duration": 4.0},
        }
        coordinator._aggregate_results()
        metrics = coordinator.get_performance_metrics()
        assert metrics["TOTAL"]["duration"] == pytest.approx(10.0)

    @pytest.mark.medium
    def test_create_micro_cycle_persists_results_succeeds(self, coordinator):
        """Parent should retain child cycle results after further cycles.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "macro"})
        micro1 = coordinator.create_micro_cycle({"description": "child1"}, Phase.EXPAND)
        with patch.object(
            micro1, "_execute_differentiate_phase", return_value={"done": True}
        ):
            micro1.progress_to_phase(Phase.DIFFERENTIATE)
        micro2 = coordinator.create_micro_cycle({"description": "child2"}, Phase.EXPAND)
        results = coordinator.results[Phase.EXPAND.name]["micro_cycle_results"]
        assert micro1.cycle_id in results
        assert micro2.cycle_id in results
        entry = results[micro1.cycle_id]
        assert entry["task"] == {"description": "child1"}
        assert {k: v for k, v in entry.items() if k != "task"} == micro1.results

    @pytest.mark.medium
    def test_micro_cycle_updates_parent_results_succeeds(self, coordinator):
        """Child cycle aggregation should refresh parent data.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "macro"})
        micro = coordinator.create_micro_cycle({"description": "child"}, Phase.EXPAND)
        with patch.object(
            micro, "_execute_differentiate_phase", return_value={"analysis": "ok"}
        ):
            micro.progress_to_phase(Phase.DIFFERENTIATE)
        entry = coordinator.results[Phase.EXPAND.name]["micro_cycle_results"][
            micro.cycle_id
        ]
        assert entry[Phase.DIFFERENTIATE.name] == {"analysis": "ok"}

    @pytest.mark.medium
    def test_human_continue_overrides_delimiting_principles_succeeds(self, coordinator):
        """A continue override should prevent termination even if other factors trigger.

        ReqID: N/A"""
        coordinator.start_cycle({"description": "macro"})
        micro_task = {
            "description": "override task",
            "human_override": "continue",
            "granularity_score": 0.1,
            "cost_score": 0.9,
            "benefit_score": 0.2,
            "quality_score": 0.95,
            "resource_usage": 0.9,
        }
        should_terminate, reason = coordinator.should_terminate_recursion(micro_task)
        assert should_terminate is False
        assert reason is None
