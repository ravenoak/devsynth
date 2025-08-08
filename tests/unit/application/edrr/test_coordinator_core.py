from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator_core import (
    EDRRCoordinatorCore,
    EDRRCoordinatorError,
)
from devsynth.application.edrr.manifest_parser import ManifestParseError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def memory_manager():
    """Create a mock memory manager for testing."""
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.store = MagicMock(return_value="memory_id_123")
    mock_memory_manager.retrieve.return_value = {
        "content": "Test memory content",
        "metadata": {"key": "value"},
    }
    mock_memory_manager.search_memory = MagicMock()
    mock_memory_manager.search_memory.return_value = [
        {
            "id": "memory_id_123",
            "content": "Test memory content",
            "metadata": {"key": "value"},
            "score": 0.95,
        }
    ]
    mock_memory_manager.stored_items = {}
    mock_memory_manager.store_with_edrr_phase = MagicMock(return_value="memory_id_456")
    mock_memory_manager.retrieve_with_edrr_phase = MagicMock()
    mock_memory_manager.retrieve_with_edrr_phase.side_effect = (
        lambda item_type, phase, metadata: mock_memory_manager.stored_items.get(
            item_type, {}
        ).get("item", {})
    )
    mock_memory_manager.retrieve_historical_patterns = MagicMock(return_value=[])
    mock_memory_manager.retrieve_relevant_knowledge = MagicMock(return_value=[])
    return mock_memory_manager


@pytest.fixture
def wsde_team():
    """Create a mock WSDE team for testing."""
    mock_wsde_team = MagicMock(spec=WSDETeam)
    mock_wsde_team.execute_task = MagicMock()
    mock_wsde_team.execute_task.return_value = {
        "result": "Task executed successfully",
        "artifacts": ["artifact1", "artifact2"],
        "metrics": {"time_taken": 10.5},
    }
    mock_wsde_team.get_team_report = MagicMock()
    mock_wsde_team.get_team_report.return_value = {
        "team_composition": ["Agent1", "Agent2", "Agent3"],
        "task_distribution": {"Agent1": 2, "Agent2": 3, "Agent3": 1},
        "performance_metrics": {"efficiency": 0.85, "quality": 0.9},
    }
    mock_wsde_team.generate_diverse_ideas = MagicMock()
    mock_wsde_team.generate_diverse_ideas.return_value = [
        {"id": 1, "idea": "Test Idea 1"},
        {"id": 2, "idea": "Test Idea 2"},
    ]
    mock_wsde_team.create_comparison_matrix = MagicMock()
    mock_wsde_team.create_comparison_matrix.return_value = {
        "idea_1": {"feasibility": 0.8},
        "idea_2": {"feasibility": 0.6},
    }
    mock_wsde_team.evaluate_options = MagicMock()
    mock_wsde_team.evaluate_options.return_value = [
        {"id": 1, "score": 0.8},
        {"id": 2, "score": 0.6},
    ]
    mock_wsde_team.analyze_trade_offs = MagicMock()
    mock_wsde_team.analyze_trade_offs.return_value = [
        {"id": 1, "trade_offs": ["Trade-off 1", "Trade-off 2"]}
    ]
    mock_wsde_team.formulate_decision_criteria = MagicMock()
    mock_wsde_team.formulate_decision_criteria.return_value = {
        "criteria_1": 0.5,
        "criteria_2": 0.5,
    }
    mock_wsde_team.select_best_option = MagicMock()
    mock_wsde_team.select_best_option.return_value = {"id": 1, "idea": "Test Idea 1"}
    mock_wsde_team.elaborate_details = MagicMock()
    mock_wsde_team.elaborate_details.return_value = [
        {"step": 1, "description": "Step 1"},
        {"step": 2, "description": "Step 2"},
    ]
    mock_wsde_team.create_implementation_plan = MagicMock()
    mock_wsde_team.create_implementation_plan.return_value = [
        {"task": 1, "description": "Task 1"},
        {"task": 2, "description": "Task 2"},
    ]
    mock_wsde_team.optimize_implementation = MagicMock()
    mock_wsde_team.optimize_implementation.return_value = {
        "optimized": True,
        "plan": [{"task": 1}, {"task": 2}],
    }
    mock_wsde_team.perform_quality_assurance = MagicMock()
    mock_wsde_team.perform_quality_assurance.return_value = {
        "issues": [],
        "recommendations": ["Recommendation 1"],
    }
    mock_wsde_team.get_primus = MagicMock()
    mock_wsde_team.get_primus.return_value = "Agent1"
    mock_wsde_team.conduct_peer_review = MagicMock()
    mock_wsde_team.conduct_peer_review.return_value = {
        "reviewer": "Agent2",
        "comments": "Looks good",
    }
    mock_wsde_team.extract_learnings = MagicMock()
    mock_wsde_team.extract_learnings.return_value = [
        {"category": "Process", "learning": "Learning 1"}
    ]
    mock_wsde_team.recognize_patterns = MagicMock()
    mock_wsde_team.recognize_patterns.return_value = [
        {"pattern": "Pattern 1", "frequency": 0.8}
    ]
    mock_wsde_team.integrate_knowledge = MagicMock()
    mock_wsde_team.integrate_knowledge.return_value = {
        "integrated": True,
        "knowledge_items": 2,
    }
    mock_wsde_team.generate_improvement_suggestions = MagicMock()
    mock_wsde_team.generate_improvement_suggestions.return_value = [
        {"phase": "EXPAND", "suggestion": "Suggestion 1"}
    ]
    return mock_wsde_team


@pytest.fixture
def code_analyzer():
    """Create a mock code analyzer for testing."""
    mock_code_analyzer = MagicMock(spec=CodeAnalyzer)
    mock_code_analyzer.analyze_code.return_value = {
        "complexity": 5,
        "maintainability": 8,
        "issues": ["Issue1", "Issue2"],
    }
    return mock_code_analyzer


@pytest.fixture
def ast_transformer():
    """Create a mock AST transformer for testing."""
    mock_ast_transformer = MagicMock(spec=AstTransformer)
    return mock_ast_transformer


@pytest.fixture
def prompt_manager():
    """Create a mock prompt manager for testing."""
    mock_prompt_manager = MagicMock(spec=PromptManager)
    return mock_prompt_manager


@pytest.fixture
def documentation_manager():
    """Create a mock documentation manager for testing."""
    mock_documentation_manager = MagicMock(spec=DocumentationManager)
    return mock_documentation_manager


@pytest.fixture
def coordinator_core(
    memory_manager,
    wsde_team,
    code_analyzer,
    ast_transformer,
    prompt_manager,
    documentation_manager,
):
    """Create an EDRRCoordinatorCore instance for testing."""
    coordinator = EDRRCoordinatorCore(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
    )
    return coordinator


class TestEDRRCoordinatorCore:
    """Tests for the EDRRCoordinatorCore class.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_initialization_succeeds(self, coordinator_core):
        """Test that the coordinator initializes correctly.

        ReqID: N/A"""
        assert coordinator_core is not None
        assert coordinator_core.memory_manager is not None
        assert coordinator_core.wsde_team is not None
        assert coordinator_core.code_analyzer is not None
        assert coordinator_core.ast_transformer is not None
        assert coordinator_core.prompt_manager is not None
        assert coordinator_core.documentation_manager is not None
        assert coordinator_core.enable_enhanced_logging is True
        assert coordinator_core.recursion_depth == 0
        assert coordinator_core.parent_cycle_id is None
        assert coordinator_core.parent_phase is None

    @pytest.mark.medium
    def test_start_cycle_succeeds(self, coordinator_core, memory_manager):
        """Test starting a new EDRR cycle.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        memory_manager.store.return_value = "task_memory_id"
        with patch.object(coordinator_core, "_aggregate_results") as mock_aggregate:
            mock_aggregate.return_value = {"status": "completed", "phases": {}}
            with patch.object(
                coordinator_core, "generate_final_report"
            ) as mock_final_report:
                mock_final_report.return_value = {
                    "report": "final report",
                    "cycle_data": {"status": "completed", "phases": {}},
                }
                coordinator_core.start_cycle(task)
                assert memory_manager.store.call_count >= 1
                assert coordinator_core.current_phase == Phase.EXPAND
                assert coordinator_core.task is not None
                assert coordinator_core.task["name"] == "Test Task"
                assert coordinator_core.task["description"] == "This is a test task"
                assert coordinator_core.task["requirements"] == ["req1", "req2"]
        assert coordinator_core.current_phase == Phase.EXPAND

    @pytest.mark.medium
    def test_start_cycle_from_manifest_succeeds(self, coordinator_core, tmp_path):
        """Test starting a cycle from a manifest file.

        ReqID: N/A"""
        manifest_path = tmp_path / "test_manifest.yaml"
        manifest_content = "\n        name: Test Task\n        description: This is a test task\n        requirements:\n          - req1\n          - req2\n        "
        manifest_path.write_text(manifest_content)
        with patch(
            "devsynth.application.edrr.coordinator_core.ManifestParser"
        ) as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse_file.return_value = {
                "name": "Test Task",
                "description": "This is a test task",
                "requirements": ["req1", "req2"],
            }
            MockManifestParser.return_value = mock_parser
            coordinator_core.start_cycle_from_manifest(manifest_path)
            MockManifestParser.assert_called_once()
            mock_parser.parse_file.assert_called_once()
            assert coordinator_core.current_phase == Phase.EXPAND

    @pytest.mark.medium
    def test_start_cycle_from_manifest_string_succeeds(self, coordinator_core):
        """Test starting a cycle from a manifest string.

        ReqID: N/A"""
        manifest_string = "\n        name: Test Task\n        description: This is a test task\n        requirements:\n          - req1\n          - req2\n        "
        with patch(
            "devsynth.application.edrr.coordinator_core.ManifestParser"
        ) as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse_string.return_value = {
                "name": "Test Task",
                "description": "This is a test task",
                "requirements": ["req1", "req2"],
            }
            MockManifestParser.return_value = mock_parser
            coordinator_core.start_cycle_from_manifest(manifest_string, is_file=False)
            MockManifestParser.assert_called_once()
            mock_parser.parse_string.assert_called_once()
            assert coordinator_core.current_phase == Phase.EXPAND

    @pytest.mark.medium
    def test_progress_to_phase_has_expected(self, coordinator_core, memory_manager):
        """Test progressing to a specific phase.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        results = coordinator_core.progress_to_phase(Phase.DIFFERENTIATE)
        assert coordinator_core.current_phase == Phase.DIFFERENTIATE
        memory_manager.store_with_edrr_phase.assert_called_with(
            results,
            phase=Phase.DIFFERENTIATE,
            tags=[
                f"phase:{Phase.DIFFERENTIATE.name}",
                f"cycle:{coordinator_core.cycle_id}",
            ],
            memory_type=MemoryType.WORKING_MEMORY,
        )

    @pytest.mark.medium
    def test_progress_to_next_phase_has_expected(self, coordinator_core):
        """Test progressing to the next phase.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        assert coordinator_core.current_phase == Phase.EXPAND
        coordinator_core.progress_to_next_phase()
        assert coordinator_core.current_phase == Phase.DIFFERENTIATE
        coordinator_core.progress_to_next_phase()
        assert coordinator_core.current_phase == Phase.REFINE
        coordinator_core.progress_to_next_phase()
        assert coordinator_core.current_phase == Phase.RETROSPECT

    @pytest.mark.medium
    def test_execute_current_phase_has_expected(self, coordinator_core):
        """Test executing the current phase.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        with patch.object(
            coordinator_core, "_execute_expand_phase"
        ) as mock_execute_expand:
            mock_execute_expand.return_value = {
                "phase": "expand",
                "status": "completed",
                "custom_field": "test value",
            }
            result = coordinator_core.execute_current_phase()
            mock_execute_expand.assert_called_once()
            assert result == {
                "phase": "expand",
                "status": "completed",
                "custom_field": "test value",
            }

    @pytest.mark.medium
    def test_generate_report_succeeds(self, coordinator_core):
        """Test generating a report.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        with patch.object(coordinator_core, "_aggregate_results") as mock_aggregate:
            mock_aggregate.return_value = {"status": "completed", "phases": {}}
            with patch.object(
                coordinator_core, "generate_final_report"
            ) as mock_final_report:
                mock_final_report.return_value = {
                    "report": "final report",
                    "cycle_data": {"status": "completed", "phases": {}},
                }
                report = coordinator_core.generate_report()
                mock_aggregate.assert_called_once()
                mock_final_report.assert_called_once_with(mock_aggregate.return_value)
                assert report == {
                    "report": "final report",
                    "cycle_data": {"status": "completed", "phases": {}},
                }

    @pytest.mark.medium
    def test_get_execution_traces_succeeds(self, coordinator_core):
        """Test getting execution traces.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        coordinator_core.execution_traces = [
            {
                "phase": "EXPAND",
                "action": "test_action",
                "timestamp": "2025-07-07T12:00:00",
            }
        ]
        traces = coordinator_core.get_execution_traces()
        assert isinstance(traces, list)
        assert len(traces) == 1
        assert traces[0]["phase"] == "EXPAND"
        assert traces[0]["action"] == "test_action"

    @pytest.mark.medium
    def test_get_execution_history_succeeds(self, coordinator_core):
        """Test getting execution history.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        history = coordinator_core.get_execution_history()
        assert isinstance(history, list)
        assert len(history) >= 1

    @pytest.mark.medium
    def test_get_performance_metrics_succeeds(self, coordinator_core):
        """Test getting performance metrics.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        metrics = coordinator_core.get_performance_metrics()
        assert isinstance(metrics, dict)
        assert "phase_durations" in metrics

    @pytest.mark.medium
    def test_decide_next_phase_has_expected(self, coordinator_core):
        """Test the internal _decide_next_phase method.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        coordinator_core.start_cycle(task)
        assert coordinator_core.current_phase == Phase.EXPAND
        next_phase = coordinator_core._decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE
        coordinator_core.progress_to_phase(Phase.DIFFERENTIATE)
        next_phase = coordinator_core._decide_next_phase()
        assert next_phase == Phase.REFINE
        coordinator_core.progress_to_phase(Phase.REFINE)
        next_phase = coordinator_core._decide_next_phase()
        assert next_phase == Phase.RETROSPECT
        coordinator_core.progress_to_phase(Phase.RETROSPECT)
        next_phase = coordinator_core._decide_next_phase()
        assert next_phase is None

    @pytest.mark.medium
    def test_maybe_auto_progress_succeeds(self, coordinator_core):
        """Test the internal _maybe_auto_progress method.

        ReqID: N/A"""
        with patch.object(coordinator_core, "start_cycle"):
            coordinator_core.current_phase = Phase.EXPAND
            coordinator_core.task = {
                "name": "Test Task",
                "description": "This is a test task",
                "requirements": ["req1", "req2"],
            }
            coordinator_core.config = {"auto_progress": True}
            with patch.object(coordinator_core, "progress_to_phase") as mock_progress:
                with patch.object(
                    coordinator_core, "_decide_next_phase"
                ) as mock_decide:
                    mock_decide.return_value = Phase.DIFFERENTIATE
                    coordinator_core._maybe_auto_progress()
                    assert mock_decide.called
                    mock_progress.assert_called_with(Phase.DIFFERENTIATE)
            coordinator_core.config = {"auto_progress": False}
            with patch.object(coordinator_core, "progress_to_phase") as mock_progress:
                coordinator_core._maybe_auto_progress()
                mock_progress.assert_not_called()

    @pytest.mark.medium
    def test_start_cycle_with_invalid_task_is_valid(self, coordinator_core):
        """Test starting a cycle with an invalid task.

        ReqID: N/A"""
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.start_cycle(None)
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.start_cycle({})

    @pytest.mark.medium
    def test_start_cycle_from_manifest_with_invalid_file_is_valid(
        self, coordinator_core
    ):
        """Test starting a cycle from an invalid manifest file.

        ReqID: N/A"""
        with patch(
            "devsynth.application.edrr.coordinator_core.ManifestParser"
        ) as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse_file.side_effect = ValueError("Invalid manifest")
            MockManifestParser.return_value = mock_parser
            with pytest.raises(ManifestParseError):
                coordinator_core.start_cycle_from_manifest("invalid_manifest.yaml")

    @pytest.mark.medium
    def test_progress_to_phase_without_cycle_has_expected(self, coordinator_core):
        """Test progressing to a phase without starting a cycle first.

        ReqID: N/A"""
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.progress_to_phase(Phase.DIFFERENTIATE)

    @pytest.mark.medium
    def test_progress_to_next_phase_without_cycle_has_expected(self, coordinator_core):
        """Test progressing to the next phase without starting a cycle first.

        ReqID: N/A"""
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.progress_to_next_phase()

    @pytest.mark.medium
    def test_execute_current_phase_without_cycle_has_expected(self, coordinator_core):
        """Test executing the current phase without starting a cycle first.

        ReqID: N/A"""
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.execute_current_phase()

    @pytest.mark.medium
    def test_generate_report_without_cycle_succeeds(self, coordinator_core):
        """Test generating a report without starting a cycle first.

        ReqID: N/A"""
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.generate_report()
