import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path

from devsynth.application.edrr.coordinator_core import EDRRCoordinatorCore, EDRRCoordinatorError
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.domain.models.memory import MemoryType


@pytest.fixture
def memory_manager():
    """Create a mock memory manager for testing."""
    mock_memory_manager = MagicMock(spec=MemoryManager)

    # Mock the store method
    mock_memory_manager.store.return_value = "memory_id_123"

    # Mock the retrieve method
    mock_memory_manager.retrieve.return_value = {
        "content": "Test memory content",
        "metadata": {"key": "value"}
    }

    # Mock the search method
    mock_memory_manager.search.return_value = [
        {
            "id": "memory_id_123",
            "content": "Test memory content",
            "metadata": {"key": "value"},
            "score": 0.95
        }
    ]

    # Set up store_with_edrr_phase to store items in a dict
    mock_memory_manager.stored_items = {}
    mock_memory_manager.store_with_edrr_phase = MagicMock()
    mock_memory_manager.store_with_edrr_phase.side_effect = (
        lambda item, item_type, phase, metadata: mock_memory_manager.stored_items.update(
            {item_type: {"item": item, "phase": phase, "metadata": metadata}}
        )
    )

    # Set up retrieve_with_edrr_phase to return items from the dict
    mock_memory_manager.retrieve_with_edrr_phase = MagicMock()
    mock_memory_manager.retrieve_with_edrr_phase.side_effect = (
        lambda item_type, phase, metadata: mock_memory_manager.stored_items.get(item_type, {}).get(
            "item", {}
        )
    )

    # Mock other methods that might be called
    mock_memory_manager.retrieve_historical_patterns = MagicMock(return_value=[])
    mock_memory_manager.retrieve_relevant_knowledge = MagicMock(return_value=[])

    return mock_memory_manager


@pytest.fixture
def wsde_team():
    """Create a mock WSDE team for testing."""
    mock_wsde_team = MagicMock(spec=WSDETeam)

    # Mock the execute_task method
    mock_wsde_team.execute_task.return_value = {
        "result": "Task executed successfully",
        "artifacts": ["artifact1", "artifact2"],
        "metrics": {"time_taken": 10.5}
    }

    # Mock the get_team_report method
    mock_wsde_team.get_team_report.return_value = {
        "team_composition": ["Agent1", "Agent2", "Agent3"],
        "task_distribution": {"Agent1": 2, "Agent2": 3, "Agent3": 1},
        "performance_metrics": {"efficiency": 0.85, "quality": 0.9}
    }

    return mock_wsde_team


@pytest.fixture
def code_analyzer():
    """Create a mock code analyzer for testing."""
    mock_code_analyzer = MagicMock(spec=CodeAnalyzer)

    # Mock the analyze_code method
    mock_code_analyzer.analyze_code.return_value = {
        "complexity": 5,
        "maintainability": 8,
        "issues": ["Issue1", "Issue2"]
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
def coordinator_core(memory_manager, wsde_team, code_analyzer, ast_transformer, prompt_manager, documentation_manager):
    """Create an EDRRCoordinatorCore instance for testing."""
    coordinator = EDRRCoordinatorCore(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True
    )
    return coordinator


class TestEDRRCoordinatorCore:
    """Tests for the EDRRCoordinatorCore class."""

    def test_initialization(self, coordinator_core):
        """Test that the coordinator initializes correctly."""
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

    def test_start_cycle(self, coordinator_core, memory_manager):
        """Test starting a new EDRR cycle."""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }

        # Mock the memory_manager.store method to return a specific ID
        memory_manager.store.return_value = "task_memory_id"

        # Call the method under test
        coordinator_core.start_cycle(task)

        # Verify that the task was stored in memory
        memory_manager.store.assert_called_with(
            content=task,
            memory_type=MemoryType.TASK,
            metadata={"cycle_id": coordinator_core.cycle_id}
        )

        # Verify that the current phase is set to EXPLORE
        assert coordinator_core.current_phase == Phase.EXPLORE

    def test_start_cycle_from_manifest(self, coordinator_core, tmp_path):
        """Test starting a cycle from a manifest file."""
        # Create a temporary manifest file
        manifest_path = tmp_path / "test_manifest.yaml"
        manifest_content = """
        name: Test Task
        description: This is a test task
        requirements:
          - req1
          - req2
        """
        manifest_path.write_text(manifest_content)

        # Mock the manifest parser
        with patch("devsynth.application.edrr.coordinator_core.ManifestParser") as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = {
                "name": "Test Task",
                "description": "This is a test task",
                "requirements": ["req1", "req2"]
            }
            MockManifestParser.return_value = mock_parser

            # Call the method under test
            coordinator_core.start_cycle_from_manifest(manifest_path)

            # Verify that the manifest parser was called
            MockManifestParser.assert_called_once()
            mock_parser.parse.assert_called_once()

            # Verify that the current phase is set to EXPLORE
            assert coordinator_core.current_phase == Phase.EXPLORE

    def test_start_cycle_from_manifest_string(self, coordinator_core):
        """Test starting a cycle from a manifest string."""
        manifest_string = """
        name: Test Task
        description: This is a test task
        requirements:
          - req1
          - req2
        """

        # Mock the manifest parser
        with patch("devsynth.application.edrr.coordinator_core.ManifestParser") as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = {
                "name": "Test Task",
                "description": "This is a test task",
                "requirements": ["req1", "req2"]
            }
            MockManifestParser.return_value = mock_parser

            # Call the method under test
            coordinator_core.start_cycle_from_manifest(manifest_string, is_file=False)

            # Verify that the manifest parser was called
            MockManifestParser.assert_called_once()
            mock_parser.parse.assert_called_once()

            # Verify that the current phase is set to EXPLORE
            assert coordinator_core.current_phase == Phase.EXPLORE

    def test_progress_to_phase(self, coordinator_core, memory_manager):
        """Test progressing to a specific phase."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Mock the memory_manager.store method to return a specific ID
        memory_manager.store.return_value = "phase_transition_memory_id"

        # Call the method under test
        coordinator_core.progress_to_phase(Phase.DESIGN)

        # Verify that the current phase is updated
        assert coordinator_core.current_phase == Phase.DESIGN

        # Verify that the phase transition was stored in memory
        memory_manager.store.assert_called_with(
            content={
                "from_phase": Phase.EXPLORE.value,
                "to_phase": Phase.DESIGN.value,
                "timestamp": pytest.approx(datetime.now().timestamp(), abs=5)
            },
            memory_type=MemoryType.PHASE_TRANSITION,
            metadata={"cycle_id": coordinator_core.cycle_id}
        )

    def test_progress_to_next_phase(self, coordinator_core):
        """Test progressing to the next phase."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # The current phase should be EXPLORE
        assert coordinator_core.current_phase == Phase.EXPLORE

        # Call the method under test
        coordinator_core.progress_to_next_phase()

        # Verify that the current phase is updated to DESIGN
        assert coordinator_core.current_phase == Phase.DESIGN

        # Progress again
        coordinator_core.progress_to_next_phase()

        # Verify that the current phase is updated to REFINE
        assert coordinator_core.current_phase == Phase.REFINE

        # Progress again
        coordinator_core.progress_to_next_phase()

        # Verify that the current phase is updated to RETROSPECT
        assert coordinator_core.current_phase == Phase.RETROSPECT

    def test_execute_current_phase(self, coordinator_core, wsde_team):
        """Test executing the current phase."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Mock the wsde_team.execute_task method
        wsde_team.execute_task.return_value = {
            "result": "Phase executed successfully",
            "artifacts": ["artifact1", "artifact2"]
        }

        # Call the method under test
        result = coordinator_core.execute_current_phase()

        # Verify that the WSDE team was called to execute the task
        wsde_team.execute_task.assert_called_once()

        # Verify the result
        assert result == {
            "result": "Phase executed successfully",
            "artifacts": ["artifact1", "artifact2"]
        }

    def test_generate_report(self, coordinator_core, wsde_team):
        """Test generating a report."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Mock the wsde_team.get_team_report method
        wsde_team.get_team_report.return_value = {
            "team_composition": ["Agent1", "Agent2", "Agent3"],
            "task_distribution": {"Agent1": 2, "Agent2": 3, "Agent3": 1},
            "performance_metrics": {"efficiency": 0.85, "quality": 0.9}
        }

        # Call the method under test
        report = coordinator_core.generate_report()

        # Verify that the WSDE team was called to get the report
        wsde_team.get_team_report.assert_called_once()

        # Verify the report structure
        assert "cycle_id" in report
        assert "task" in report
        assert "phases" in report
        assert "team_report" in report
        assert report["team_report"] == wsde_team.get_team_report.return_value

    def test_get_execution_traces(self, coordinator_core):
        """Test getting execution traces."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Call the method under test
        traces = coordinator_core.get_execution_traces()

        # Verify the traces structure
        assert isinstance(traces, dict)
        assert "cycle_id" in traces
        assert "phases" in traces

    def test_get_execution_history(self, coordinator_core):
        """Test getting execution history."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Call the method under test
        history = coordinator_core.get_execution_history()

        # Verify the history structure
        assert isinstance(history, list)
        # The history should contain at least the cycle start event
        assert len(history) >= 1

    def test_get_performance_metrics(self, coordinator_core):
        """Test getting performance metrics."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Call the method under test
        metrics = coordinator_core.get_performance_metrics()

        # Verify the metrics structure
        assert isinstance(metrics, dict)
        assert "cycle_duration" in metrics
        assert "phase_durations" in metrics

    def test_decide_next_phase(self, coordinator_core):
        """Test the internal _decide_next_phase method."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # The current phase should be EXPLORE
        assert coordinator_core.current_phase == Phase.EXPLORE

        # Call the internal method under test
        next_phase = coordinator_core._decide_next_phase()

        # Verify that the next phase is DESIGN
        assert next_phase == Phase.DESIGN

        # Progress to DESIGN
        coordinator_core.progress_to_phase(Phase.DESIGN)

        # Call the internal method again
        next_phase = coordinator_core._decide_next_phase()

        # Verify that the next phase is REFINE
        assert next_phase == Phase.REFINE

        # Progress to REFINE
        coordinator_core.progress_to_phase(Phase.REFINE)

        # Call the internal method again
        next_phase = coordinator_core._decide_next_phase()

        # Verify that the next phase is RETROSPECT
        assert next_phase == Phase.RETROSPECT

        # Progress to RETROSPECT
        coordinator_core.progress_to_phase(Phase.RETROSPECT)

        # Call the internal method again
        next_phase = coordinator_core._decide_next_phase()

        # Verify that there is no next phase (we're at the end)
        assert next_phase is None

    def test_maybe_auto_progress(self, coordinator_core):
        """Test the internal _maybe_auto_progress method."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        coordinator_core.start_cycle(task)

        # Mock the config to enable auto-progress
        coordinator_core.config = {"auto_progress": True}

        # Call the internal method under test
        coordinator_core._maybe_auto_progress()

        # Verify that the current phase is updated to DESIGN (auto-progressed)
        assert coordinator_core.current_phase == Phase.DESIGN

        # Disable auto-progress
        coordinator_core.config = {"auto_progress": False}

        # Call the internal method again
        coordinator_core._maybe_auto_progress()

        # Verify that the current phase is still DESIGN (no auto-progress)
        assert coordinator_core.current_phase == Phase.DESIGN

    def test_start_cycle_with_invalid_task(self, coordinator_core):
        """Test starting a cycle with an invalid task."""
        # Try to start a cycle with None
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.start_cycle(None)

        # Try to start a cycle with an empty dict
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.start_cycle({})

    def test_start_cycle_from_manifest_with_invalid_file(self, coordinator_core):
        """Test starting a cycle from an invalid manifest file."""
        # Mock the manifest parser to raise an exception
        with patch("devsynth.application.edrr.coordinator_core.ManifestParser") as MockManifestParser:
            mock_parser = MagicMock()
            mock_parser.parse.side_effect = ManifestParseError("Invalid manifest")
            MockManifestParser.return_value = mock_parser

            # Try to start a cycle from an invalid manifest
            with pytest.raises(EDRRCoordinatorError):
                coordinator_core.start_cycle_from_manifest("invalid_manifest.yaml")

    def test_progress_to_phase_without_cycle(self, coordinator_core):
        """Test progressing to a phase without starting a cycle first."""
        # Try to progress to a phase without starting a cycle
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.progress_to_phase(Phase.DESIGN)

    def test_progress_to_next_phase_without_cycle(self, coordinator_core):
        """Test progressing to the next phase without starting a cycle first."""
        # Try to progress to the next phase without starting a cycle
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.progress_to_next_phase()

    def test_execute_current_phase_without_cycle(self, coordinator_core):
        """Test executing the current phase without starting a cycle first."""
        # Try to execute the current phase without starting a cycle
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.execute_current_phase()

    def test_generate_report_without_cycle(self, coordinator_core):
        """Test generating a report without starting a cycle first."""
        # Try to generate a report without starting a cycle
        with pytest.raises(EDRRCoordinatorError):
            coordinator_core.generate_report()
