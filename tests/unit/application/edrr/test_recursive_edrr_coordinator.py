"""Tests for the recursive functionality of the EDRRCoordinator class."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)


@pytest.fixture
def memory_manager():
    """Create a mock memory manager."""
    mock = MagicMock(spec=MemoryManager)
    # Set up store_with_edrr_phase to store items in a dict
    mock.stored_items = {}
    mock.store_with_edrr_phase.side_effect = (
        lambda item, item_type, phase, metadata: mock.stored_items.update(
            {item_type: {"item": item, "phase": phase, "metadata": metadata}}
        )
    )
    # Set up retrieve_with_edrr_phase to return items from the dict
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
    """Tests for the recursive functionality of the EDRRCoordinator class."""

    def test_initialization_with_recursion_support(self, coordinator):
        """Test that the coordinator is initialized with recursion support."""
        assert hasattr(coordinator, "parent_cycle_id")
        assert hasattr(coordinator, "recursion_depth")
        assert hasattr(coordinator, "child_cycles")
        assert coordinator.parent_cycle_id is None
        assert coordinator.recursion_depth == 0
        assert coordinator.child_cycles == []

    def test_create_micro_cycle(self, coordinator):
        """Test creating a micro-EDRR cycle."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})
        macro_cycle_id = coordinator.cycle_id

        # Create a micro cycle
        micro_task = {"description": "Micro Task"}
        micro_cycle = coordinator.create_micro_cycle(micro_task, Phase.EXPAND)

        # Verify the micro cycle was created correctly
        assert micro_cycle is not None
        assert micro_cycle.parent_cycle_id == macro_cycle_id
        assert micro_cycle.recursion_depth == 1
        assert micro_cycle.task == micro_task
        assert micro_cycle in coordinator.child_cycles

    def test_recursion_depth_limit(self, coordinator):
        """Test that recursion depth is limited."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Create micro cycles up to the maximum depth
        current_cycle = coordinator
        for i in range(1, coordinator.max_recursion_depth + 1):
            micro_task = {"description": f"Micro Task Level {i}"}
            current_cycle = current_cycle.create_micro_cycle(micro_task, Phase.EXPAND)
            assert current_cycle.recursion_depth == i

        # Attempt to create a cycle beyond the maximum depth
        with pytest.raises(EDRRCoordinatorError):
            current_cycle.create_micro_cycle({"description": "Too Deep"}, Phase.EXPAND)

    def test_create_micro_cycle_terminated(self, coordinator):
        coordinator.start_cycle({"description": "Macro"})
        with patch.object(coordinator, "should_terminate_recursion", return_value=True):
            with pytest.raises(EDRRCoordinatorError):
                coordinator.create_micro_cycle({"description": "Sub"}, Phase.EXPAND)
        assert not coordinator.child_cycles

    def test_micro_edrr_within_expand_phase(self, coordinator):
        """Test micro-EDRR cycles within the Expand phase."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Mock the _execute_expand_phase method to create micro cycles
        original_execute = coordinator._execute_expand_phase

        def mock_execute_expand(context=None):
            # Create micro cycles for different aspects of expansion
            coordinator.create_micro_cycle(
                {"description": "Brainstorm Ideas"}, Phase.EXPAND
            )
            coordinator.create_micro_cycle(
                {"description": "Research Existing Solutions"}, Phase.EXPAND
            )
            coordinator.create_micro_cycle(
                {"description": "Analyze Requirements"}, Phase.EXPAND
            )

            # Call the original method to maintain normal behavior
            return original_execute(context)

        coordinator._execute_expand_phase = mock_execute_expand

        # Execute the expand phase
        coordinator.execute_current_phase()

        # Verify micro cycles were created
        assert len(coordinator.child_cycles) == 3
        assert all(
            cycle.parent_cycle_id == coordinator.cycle_id
            for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    def test_micro_edrr_within_differentiate_phase(self, coordinator):
        """Test micro-EDRR cycles within the Differentiate phase."""
        # Start a macro cycle and progress to Differentiate
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)

        # Mock the _execute_differentiate_phase method to create micro cycles
        original_execute = coordinator._execute_differentiate_phase

        def mock_execute_differentiate(context=None):
            # Create micro cycles for different aspects of differentiation
            coordinator.create_micro_cycle(
                {"description": "Compare Approaches"}, Phase.DIFFERENTIATE
            )
            coordinator.create_micro_cycle(
                {"description": "Evaluate Trade-offs"}, Phase.DIFFERENTIATE
            )
            coordinator.create_micro_cycle(
                {"description": "Select Best Approach"}, Phase.DIFFERENTIATE
            )

            # Call the original method to maintain normal behavior
            return original_execute(context)

        coordinator._execute_differentiate_phase = mock_execute_differentiate

        # Execute the differentiate phase
        coordinator.execute_current_phase()

        # Verify micro cycles were created
        assert len(coordinator.child_cycles) == 3
        assert all(
            cycle.parent_cycle_id == coordinator.cycle_id
            for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    def test_micro_edrr_within_refine_phase(self, coordinator):
        """Test micro-EDRR cycles within the Refine phase."""
        # Start a macro cycle and progress to Refine
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.REFINE)

        # Mock the _execute_refine_phase method to create micro cycles
        original_execute = coordinator._execute_refine_phase

        def mock_execute_refine(context=None):
            # Create micro cycles for different aspects of refinement
            coordinator.create_micro_cycle(
                {"description": "Implement Solution"}, Phase.REFINE
            )
            coordinator.create_micro_cycle(
                {"description": "Optimize Performance"}, Phase.REFINE
            )
            coordinator.create_micro_cycle(
                {"description": "Ensure Quality"}, Phase.REFINE
            )

            # Call the original method to maintain normal behavior
            return original_execute(context)

        coordinator._execute_refine_phase = mock_execute_refine

        # Execute the refine phase
        coordinator.execute_current_phase()

        # Verify micro cycles were created
        assert len(coordinator.child_cycles) == 3
        assert all(
            cycle.parent_cycle_id == coordinator.cycle_id
            for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    def test_micro_edrr_within_retrospect_phase(self, coordinator):
        """Test micro-EDRR cycles within the Retrospect phase."""
        # Start a macro cycle and progress to Retrospect
        coordinator.start_cycle({"description": "Macro Task"})
        coordinator.progress_to_phase(Phase.RETROSPECT)

        # Mock the _execute_retrospect_phase method to create micro cycles
        original_execute = coordinator._execute_retrospect_phase

        def mock_execute_retrospect(context=None):
            # Create micro cycles for different aspects of retrospection
            coordinator.create_micro_cycle(
                {"description": "Extract Learnings"}, Phase.RETROSPECT
            )
            coordinator.create_micro_cycle(
                {"description": "Identify Patterns"}, Phase.RETROSPECT
            )
            coordinator.create_micro_cycle(
                {"description": "Generate Improvements"}, Phase.RETROSPECT
            )

            # Call the original method to maintain normal behavior
            return original_execute(context)

        coordinator._execute_retrospect_phase = mock_execute_retrospect

        # Execute the retrospect phase
        coordinator.execute_current_phase()

        # Verify micro cycles were created
        assert len(coordinator.child_cycles) == 3
        assert all(
            cycle.parent_cycle_id == coordinator.cycle_id
            for cycle in coordinator.child_cycles
        )
        assert all(cycle.recursion_depth == 1 for cycle in coordinator.child_cycles)

    def test_granularity_threshold_check(self, coordinator):
        """Test granularity threshold check for recursion termination."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Test with a task that is too granular
        micro_task = {"description": "Very small task", "granularity_score": 0.1}
        assert coordinator.should_terminate_recursion(micro_task) == True

        # Test with a task that is not too granular
        micro_task = {"description": "Complex task", "granularity_score": 0.8}
        assert coordinator.should_terminate_recursion(micro_task) == False

    def test_cost_benefit_analysis(self, coordinator):
        """Test cost-benefit analysis for recursion termination."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Test with a task where cost exceeds benefit
        micro_task = {
            "description": "High cost task",
            "cost_score": 0.9,
            "benefit_score": 0.2,
        }
        assert coordinator.should_terminate_recursion(micro_task) == True

        # Test with a task where benefit exceeds cost
        micro_task = {
            "description": "High benefit task",
            "cost_score": 0.3,
            "benefit_score": 0.8,
        }
        assert coordinator.should_terminate_recursion(micro_task) == False

    @pytest.mark.parametrize(
        "micro_task",
        [
            {"description": "Too granular", "granularity_score": 0.1},
            {
                "description": "Too costly",
                "cost_score": 0.9,
                "benefit_score": 0.2,
            },
        ],
    )
    def test_create_micro_cycle_termination(self, coordinator, micro_task):
        """create_micro_cycle should abort when delimiting principles trigger."""
        coordinator.start_cycle({"description": "Macro Task"})

        assert coordinator.should_terminate_recursion(micro_task) is True
        with pytest.raises(EDRRCoordinatorError):
            coordinator.create_micro_cycle(micro_task, Phase.EXPAND)
        assert not coordinator.child_cycles

    def test_quality_threshold_monitoring(self, coordinator):
        """Test quality threshold monitoring for recursion termination."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Test with a task that already meets quality threshold
        micro_task = {"description": "High quality task", "quality_score": 0.95}
        assert coordinator.should_terminate_recursion(micro_task) == True

        # Test with a task that doesn't meet quality threshold
        micro_task = {"description": "Low quality task", "quality_score": 0.5}
        assert coordinator.should_terminate_recursion(micro_task) == False

    def test_resource_limits(self, coordinator):
        """Test resource limits for recursion termination."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Test with a task that would exceed resource limits
        micro_task = {"description": "Resource intensive task", "resource_usage": 0.9}
        assert coordinator.should_terminate_recursion(micro_task) == True

        # Test with a task within resource limits
        micro_task = {"description": "Lightweight task", "resource_usage": 0.2}
        assert coordinator.should_terminate_recursion(micro_task) == False

    def test_human_judgment_override(self, coordinator):
        """Test human judgment override for recursion termination."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})

        # Test with a task that has human override to terminate
        micro_task = {
            "description": "Task with override",
            "human_override": "terminate",
        }
        assert coordinator.should_terminate_recursion(micro_task) == True

        # Test with a task that has human override to continue
        micro_task = {"description": "Task with override", "human_override": "continue"}
        assert coordinator.should_terminate_recursion(micro_task) == False

        # Test with a task without human override
        micro_task = {"description": "Task without override"}
        # Should fall back to other criteria
        assert coordinator.should_terminate_recursion(micro_task) in [True, False]

    def test_recursive_execution_tracking(self, coordinator):
        """Test tracking of recursive execution."""
        # Start a macro cycle
        coordinator.start_cycle({"description": "Macro Task"})
        macro_cycle_id = coordinator.cycle_id

        # Create and execute a micro cycle
        micro_cycle = coordinator.create_micro_cycle(
            {"description": "Micro Task"}, Phase.EXPAND
        )
        micro_cycle.execute_current_phase()

        # Verify execution traces include recursive information
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

    def test_auto_micro_cycle_creation(self, coordinator):
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

    def test_create_micro_cycle_max_depth_stop(self, coordinator):
        """Ensure micro cycle creation fails when max depth is reached."""
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

    def test_decide_next_phase_phase_complete(self, coordinator):
        """_decide_next_phase should transition when phase is complete."""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name]["phase_complete"] = True
        next_phase = coordinator._decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    def test_decide_next_phase_timeout(self, coordinator):
        """_decide_next_phase should transition after timeout."""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name].pop("phase_complete", None)
        coordinator.phase_transition_timeout = 1
        coordinator._phase_start_times[Phase.EXPAND] = datetime.now() - timedelta(
            seconds=2
        )
        next_phase = coordinator._decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    def test_decide_next_phase_no_transition(self, coordinator):
        """_decide_next_phase should return None when conditions not met."""
        coordinator.start_cycle({"description": "Task"})
        coordinator.results[Phase.EXPAND.name].pop("phase_complete", None)
        coordinator.phase_transition_timeout = 100
        coordinator._phase_start_times[Phase.EXPAND] = datetime.now()
        assert coordinator._decide_next_phase() is None

    def test_should_terminate_recursion_all_factors_true(self, coordinator):
        """If all delimiting principles trigger, recursion should terminate."""
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
        assert coordinator.should_terminate_recursion(task) is True

    def test_should_terminate_recursion_all_factors_false(self, coordinator):
        """If no delimiting principle triggers, recursion should continue."""
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
        assert coordinator.should_terminate_recursion(task) is False

    def test_get_performance_metrics_total_duration(self, coordinator):
        """get_performance_metrics should report aggregated duration."""
        coordinator.performance_metrics = {
            Phase.EXPAND.name: {"duration": 1.0},
            Phase.DIFFERENTIATE.name: {"duration": 2.0},
            Phase.REFINE.name: {"duration": 3.0},
            Phase.RETROSPECT.name: {"duration": 4.0},
        }
        coordinator._aggregate_results()
        metrics = coordinator.get_performance_metrics()
        assert metrics["TOTAL"]["duration"] == pytest.approx(10.0)

    def test_create_micro_cycle_persists_results(self, coordinator):
        """Parent should retain child cycle results after further cycles."""
        coordinator.start_cycle({"description": "macro"})
        micro1 = coordinator.create_micro_cycle({"description": "child1"}, Phase.EXPAND)
        with patch.object(
            micro1, "_execute_differentiate_phase", return_value={"done": True}
        ):
            micro1.progress_to_phase(Phase.DIFFERENTIATE)

        # Create a second child cycle
        micro2 = coordinator.create_micro_cycle({"description": "child2"}, Phase.EXPAND)

        results = coordinator.results[Phase.EXPAND.name]["micro_cycle_results"]
        assert micro1.cycle_id in results
        assert micro2.cycle_id in results
        entry = results[micro1.cycle_id]
        assert entry["task"] == {"description": "child1"}
        assert {k: v for k, v in entry.items() if k != "task"} == micro1.results

    def test_micro_cycle_updates_parent_results(self, coordinator):
        """Child cycle aggregation should refresh parent data."""
        coordinator.start_cycle({"description": "macro"})
        micro = coordinator.create_micro_cycle({"description": "child"}, Phase.EXPAND)
        with patch.object(micro, "_execute_differentiate_phase", return_value={"analysis": "ok"}):
            micro.progress_to_phase(Phase.DIFFERENTIATE)

        entry = coordinator.results[Phase.EXPAND.name]["micro_cycle_results"][micro.cycle_id]
        assert entry[Phase.DIFFERENTIATE.name] == {"analysis": "ok"}

    def test_human_continue_overrides_delimiting_principles(self, coordinator):
        """A continue override should prevent termination even if other factors trigger."""
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
        assert coordinator.should_terminate_recursion(micro_task) is False
