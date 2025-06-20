"""Tests for the EDRRCoordinator class."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

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


class TestEDRRCoordinator:
    """Tests for the EDRRCoordinator class."""

    def test_initialization(self, coordinator):
        """Test that the coordinator is initialized correctly."""
        assert coordinator.memory_manager is not None
        assert coordinator.wsde_team is not None
        assert coordinator.code_analyzer is not None
        assert coordinator.ast_transformer is not None
        assert coordinator.prompt_manager is not None
        assert coordinator.documentation_manager is not None
        assert coordinator._enable_enhanced_logging is True
        assert coordinator._execution_traces == {}

    def test_start_cycle(self, coordinator, memory_manager):
        """Test starting a new EDRR cycle."""
        task = {"description": "Test Task", "requirements": ["Req 1", "Req 2"]}
        coordinator.start_cycle(task)

        assert coordinator.task == task
        assert coordinator.cycle_id is not None
        assert coordinator.current_phase == Phase.EXPAND
        assert memory_manager.store_with_edrr_phase.call_count >= 1

    def test_expand_phase_execution(
        self, coordinator, memory_manager, wsde_team, code_analyzer
    ):
        """Test executing the Expand phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"
        coordinator.current_phase = Phase.EXPAND

        results = coordinator._execute_expand_phase({})

        assert "ideas" in results
        assert "knowledge" in results
        assert "code_elements" in results
        assert wsde_team.generate_diverse_ideas.call_count == 1
        assert memory_manager.retrieve_relevant_knowledge.call_count == 1
        assert code_analyzer.analyze_project_structure.call_count == 1
        assert memory_manager.store_with_edrr_phase.call_count >= 1
        assert f"EXPAND_{coordinator.cycle_id}" in coordinator._execution_traces

    def test_differentiate_phase_execution(
        self, coordinator, memory_manager, wsde_team
    ):
        """Test executing the Differentiate phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"
        coordinator.current_phase = Phase.DIFFERENTIATE

        # Setup memory manager to return Expand phase results
        memory_manager.stored_items = {
            "EXPAND_RESULTS": {
                "item": {"ideas": [{"id": 1}, {"id": 2}]},
                "phase": "EXPAND",
                "metadata": {"cycle_id": "test-cycle-id"},
            }
        }

        results = coordinator._execute_differentiate_phase({})

        assert "comparison_matrix" in results
        assert "evaluated_options" in results
        assert "trade_offs" in results
        assert "decision_criteria" in results
        assert wsde_team.create_comparison_matrix.call_count == 1
        assert wsde_team.evaluate_options.call_count == 1
        assert wsde_team.analyze_trade_offs.call_count == 1
        assert wsde_team.formulate_decision_criteria.call_count == 1
        assert memory_manager.store_with_edrr_phase.call_count >= 1
        assert f"DIFFERENTIATE_{coordinator.cycle_id}" in coordinator._execution_traces

    def test_refine_phase_execution(self, coordinator, memory_manager, wsde_team):
        """Test executing the Refine phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"
        coordinator.current_phase = Phase.REFINE

        # Setup memory manager to return Differentiate phase results
        memory_manager.stored_items = {
            "DIFFERENTIATE_RESULTS": {
                "item": {
                    "evaluated_options": [{"id": 1}, {"id": 2}],
                    "decision_criteria": {"criteria_1": 0.5, "criteria_2": 0.5},
                },
                "phase": "DIFFERENTIATE",
                "metadata": {"cycle_id": "test-cycle-id"},
            }
        }

        results = coordinator._execute_refine_phase({})

        assert "selected_option" in results
        assert "detailed_plan" in results
        assert "implementation_plan" in results
        assert "optimized_plan" in results
        assert "quality_checks" in results
        assert wsde_team.select_best_option.call_count == 1
        assert wsde_team.elaborate_details.call_count == 1
        assert wsde_team.create_implementation_plan.call_count == 1
        assert wsde_team.optimize_implementation.call_count == 1
        assert wsde_team.perform_quality_assurance.call_count == 1
        assert memory_manager.store_with_edrr_phase.call_count >= 1
        assert f"REFINE_{coordinator.cycle_id}" in coordinator._execution_traces

    def test_retrospect_phase_execution(self, coordinator, memory_manager, wsde_team):
        """Test executing the Retrospect phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"
        coordinator.current_phase = Phase.RETROSPECT

        # Setup memory manager to return previous phase results
        memory_manager.stored_items = {
            "EXPAND_RESULTS": {
                "item": {"ideas": [{"id": 1}, {"id": 2}]},
                "phase": "EXPAND",
                "metadata": {"cycle_id": "test-cycle-id"},
            },
            "DIFFERENTIATE_RESULTS": {
                "item": {
                    "evaluated_options": [{"id": 1}, {"id": 2}],
                    "decision_criteria": {"criteria_1": 0.5, "criteria_2": 0.5},
                },
                "phase": "DIFFERENTIATE",
                "metadata": {"cycle_id": "test-cycle-id"},
            },
            "REFINE_RESULTS": {
                "item": {
                    "implementation_plan": [{"task": 1}, {"task": 2}],
                    "quality_checks": {"issues": [], "recommendations": []},
                },
                "phase": "REFINE",
                "metadata": {"cycle_id": "test-cycle-id"},
            },
        }

        results = coordinator._execute_retrospect_phase({})

        assert "learnings" in results
        assert "patterns" in results
        assert "integrated_knowledge" in results
        assert "improvement_suggestions" in results
        assert "final_report" in results
        assert wsde_team.extract_learnings.call_count == 1
        assert wsde_team.recognize_patterns.call_count == 1
        assert wsde_team.integrate_knowledge.call_count == 1
        assert wsde_team.generate_improvement_suggestions.call_count == 1
        assert (
            memory_manager.store_with_edrr_phase.call_count >= 2
        )  # Store retrospect results and final report
        assert f"RETROSPECT_{coordinator.cycle_id}" in coordinator._execution_traces

    def test_generate_final_report(self, coordinator):
        """Test generating the final report."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"

        cycle_data = {
            "task": {"description": "Test Task"},
            "expand": {"ideas": [{"id": 1}, {"id": 2}], "knowledge": []},
            "differentiate": {
                "evaluated_options": [{"id": 1}, {"id": 2}],
                "trade_offs": [],
                "decision_criteria": {},
            },
            "refine": {
                "implementation_plan": [{"task": 1}, {"task": 2}],
                "quality_checks": {},
            },
            "retrospect": {
                "learnings": [],
                "patterns": [],
                "improvement_suggestions": [],
            },
        }

        report = coordinator.generate_final_report(cycle_data)

        assert "title" in report
        assert "cycle_id" in report
        assert "timestamp" in report
        assert "task_summary" in report
        assert "process_summary" in report
        assert "outcome" in report
        assert report["cycle_id"] == coordinator.cycle_id
        assert "expand" in report["process_summary"]
        assert "differentiate" in report["process_summary"]
        assert "refine" in report["process_summary"]
        assert "retrospect" in report["process_summary"]

    def test_execute_current_phase(self, coordinator):
        """Test executing the current phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"

        # Test with no current phase
        coordinator.current_phase = None
        with pytest.raises(EDRRCoordinatorError):
            coordinator.execute_current_phase()

        # Test with Expand phase
        coordinator.current_phase = Phase.EXPAND
        with patch.object(
            coordinator, "_execute_expand_phase", return_value={"ideas": []}
        ):
            results = coordinator.execute_current_phase()
            assert "ideas" in results
            assert "EXPAND" in coordinator.results

        # Test with exception in phase execution
        with patch.object(
            coordinator, "_execute_expand_phase", side_effect=Exception("Test error")
        ):
            with pytest.raises(EDRRCoordinatorError):
                coordinator.execute_current_phase()

    def test_progress_to_phase(self, coordinator, memory_manager):
        """Test progressing to a phase."""
        coordinator.task = {"description": "Test Task"}
        coordinator.cycle_id = "test-cycle-id"

        # Mock the phase execution methods
        with patch.object(coordinator, "_execute_expand_phase"):
            coordinator.progress_to_phase(Phase.EXPAND)
            assert coordinator.current_phase == Phase.EXPAND
            assert memory_manager.store_with_edrr_phase.call_count >= 1

        # Test with manifest
        coordinator.manifest = {}
        coordinator.manifest_parser = MagicMock()
        coordinator.manifest_parser.check_phase_dependencies.return_value = True

        with patch.object(coordinator, "_execute_differentiate_phase"):
            coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            assert coordinator.current_phase == Phase.DIFFERENTIATE
            assert coordinator.manifest_parser.start_phase.call_count == 1
            assert coordinator.manifest_parser.complete_phase.call_count == 1

        # Test dependency failure
        coordinator.current_phase = Phase.EXPAND
        coordinator.manifest_parser.check_phase_dependencies.return_value = False
        with pytest.raises(EDRRCoordinatorError):
            coordinator.progress_to_phase(Phase.DIFFERENTIATE)

    def test_full_cycle(self, coordinator):
        """Test a full EDRR cycle."""
        task = {"description": "Test Task", "requirements": ["Req 1", "Req 2"]}

        # Mock the phase execution methods
        with patch.object(
            coordinator, "_execute_expand_phase", return_value={"ideas": []}
        ), patch.object(
            coordinator,
            "_execute_differentiate_phase",
            return_value={"evaluated_options": []},
        ), patch.object(
            coordinator,
            "_execute_refine_phase",
            return_value={"implementation_plan": []},
        ), patch.object(
            coordinator, "_execute_retrospect_phase", return_value={"learnings": []}
        ):

            # Start the cycle
            coordinator.start_cycle(task)
            assert coordinator.current_phase == Phase.EXPAND

            # Progress through phases
            coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            assert coordinator.current_phase == Phase.DIFFERENTIATE

            coordinator.progress_to_phase(Phase.REFINE)
            assert coordinator.current_phase == Phase.REFINE

            coordinator.progress_to_phase(Phase.RETROSPECT)
            assert coordinator.current_phase == Phase.RETROSPECT

            # Check that results were collected
            assert "EXPAND" in coordinator.results
            assert "DIFFERENTIATE" in coordinator.results
            assert "REFINE" in coordinator.results
            assert "RETROSPECT" in coordinator.results

    def test_progress_to_next_phase(self, coordinator):
        task = {"description": "Test"}
        with patch.object(
            coordinator, "_execute_expand_phase", return_value={}
        ), patch.object(
            coordinator, "_execute_differentiate_phase", return_value={}
        ), patch.object(
            coordinator, "_execute_refine_phase", return_value={}
        ), patch.object(
            coordinator, "_execute_retrospect_phase", return_value={}
        ):
            coordinator.start_cycle(task)
            assert coordinator.current_phase == Phase.EXPAND
            coordinator.progress_to_next_phase()
            assert coordinator.current_phase == Phase.DIFFERENTIATE
            coordinator.progress_to_next_phase()
            assert coordinator.current_phase == Phase.REFINE
            coordinator.progress_to_next_phase()
            assert coordinator.current_phase == Phase.RETROSPECT
            with pytest.raises(EDRRCoordinatorError):
                coordinator.progress_to_next_phase()

    def test_progress_to_next_phase_without_current(self, coordinator):
        """progress_to_next_phase should fail if no phase is active."""
        with pytest.raises(EDRRCoordinatorError):
            coordinator.progress_to_next_phase()

    def test_start_cycle_from_manifest(self, coordinator):
        manifest_parser = MagicMock()
        manifest_parser.parse_file.return_value = {
            "id": "test-id",
            "description": "desc",
            "phases": {
                "expand": {"instructions": ""},
                "differentiate": {"instructions": ""},
                "refine": {"instructions": ""},
                "retrospect": {"instructions": ""},
            },
        }
        manifest_parser.get_manifest_id.return_value = "test-id"
        manifest_parser.get_manifest_description.return_value = "desc"
        manifest_parser.get_manifest_metadata.return_value = {}
        manifest_parser.execution_trace = {"start_time": "now"}
        manifest_parser.start_execution.return_value = None
        coordinator.manifest_parser = manifest_parser

        with patch.object(coordinator, "progress_to_phase") as progress_mock:
            coordinator.start_cycle_from_manifest("path.json")

        manifest_parser.parse_file.assert_called_once_with("path.json")
        progress_mock.assert_called_once_with(Phase.EXPAND)
        assert coordinator.task["id"] == "test-id"
        assert coordinator.manifest == manifest_parser.parse_file.return_value

    def test_maybe_create_micro_cycles(self, coordinator):
        context = {"micro_tasks": [{"description": "sub"}]}
        results = {}
        micro = MagicMock()
        micro.cycle_id = "cid"
        micro.results = {"phase_complete": True}
        with patch.object(
            coordinator, "create_micro_cycle", return_value=micro
        ) as create_mock:
            coordinator._maybe_create_micro_cycles(context, Phase.EXPAND, results)
        create_mock.assert_called_once_with({"description": "sub"}, Phase.EXPAND)
        assert results["micro_cycle_results"]["cid"] == micro.results
