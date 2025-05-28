"""
Integration tests for GraphMemoryAdapter and EDRRCoordinator.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock

from devsynth.methodology.base import Phase
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.domain.models.memory import MemoryItem, MemoryType


class TestGraphMemoryEDRRIntegration:
    """Integration tests for GraphMemoryAdapter and EDRRCoordinator."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def graph_adapter(self, temp_dir):
        """Create a GraphMemoryAdapter instance for testing."""
        return GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for the EDRRCoordinator."""
        wsde_team = MagicMock()
        code_analyzer = MagicMock()
        ast_transformer = MagicMock()
        prompt_manager = MagicMock()
        documentation_manager = MagicMock()

        # Set up mock WSDE team to return some approaches
        approaches = [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
        wsde_team.brainstorm_approaches.return_value = approaches

        # Set up mock WSDE team to return an evaluation
        evaluation = {
            "selected_approach": approaches[0],
            "rationale": "This approach is better"
        }
        wsde_team.evaluate_approaches.return_value = evaluation

        # Set up mock WSDE team to return an implementation
        implementation = {
            "code": "def approach1_improved(): return 'Hello, World!'",
            "description": "Improved implementation"
        }
        wsde_team.implement_approach.return_value = implementation

        # Set up mock WSDE team to return an evaluation of the implementation
        implementation_evaluation = {
            "quality": "good",
            "issues": [],
            "suggestions": []
        }
        wsde_team.evaluate_implementation.return_value = implementation_evaluation

        return {
            "wsde_team": wsde_team,
            "code_analyzer": code_analyzer,
            "ast_transformer": ast_transformer,
            "prompt_manager": prompt_manager,
            "documentation_manager": documentation_manager
        }

    @pytest.fixture
    def coordinator(self, graph_adapter, mock_dependencies):
        """Create an EDRRCoordinator instance with a GraphMemoryAdapter for testing."""
        return EDRRCoordinator(
            memory_manager=graph_adapter,
            wsde_team=mock_dependencies["wsde_team"],
            code_analyzer=mock_dependencies["code_analyzer"],
            ast_transformer=mock_dependencies["ast_transformer"],
            prompt_manager=mock_dependencies["prompt_manager"],
            documentation_manager=mock_dependencies["documentation_manager"],
            enable_enhanced_logging=True
        )

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return {
            "id": "task-123",
            "description": "Implement a feature",
            "code": "def example(): pass"
        }

    def test_edrr_cycle_with_graph_memory(self, coordinator, graph_adapter, sample_task, mock_dependencies):
        """Test a complete EDRR cycle with GraphMemoryAdapter integration."""
        # Start the EDRR cycle
        coordinator.start_cycle(sample_task)

        # Check that the task was stored in the graph memory
        task_items = graph_adapter.search({"type": "TASK"})
        assert len(task_items) > 0
        print(f"Task item content: {task_items[0].content}")
        print(f"Task item content type: {type(task_items[0].content)}")

        # If content is a string, try to access the task directly
        if isinstance(task_items[0].content, str):
            assert sample_task["id"] in task_items[0].content
            assert sample_task["description"] in task_items[0].content
        else:
            # Original assertions for dictionary content
            assert task_items[0].content["id"] == sample_task["id"]
            assert task_items[0].content["description"] == sample_task["description"]

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            coordinator.progress_to_phase(phase)

            # Check that the phase transition was stored in the graph memory
            phase_transitions = graph_adapter.search({"type": "PHASE_TRANSITION"})
            assert len(phase_transitions) > 0

        # Generate the final report
        report = coordinator.generate_report()

        # Check that the report includes all phases
        assert "EXPAND" in report["phases"]
        assert "DIFFERENTIATE" in report["phases"]
        assert "REFINE" in report["phases"]
        assert "RETROSPECT" in report["phases"]

        # Check that execution traces are available
        traces = coordinator.get_execution_traces()
        assert "cycle_id" in traces
        assert "phases" in traces

        # Check that the execution history is stored in the graph memory
        history = coordinator.get_execution_history()
        assert len(history) >= 4  # At least one entry per phase

    def test_memory_volatility_with_edrr(self, coordinator, graph_adapter, sample_task):
        """Test memory volatility controls with EDRR integration."""
        # Start the EDRR cycle
        coordinator.start_cycle(sample_task)

        # Add memory volatility controls
        graph_adapter.add_memory_volatility(decay_rate=0.3, threshold=0.5, advanced_controls=True)

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            coordinator.progress_to_phase(phase)

        # Apply memory decay
        volatile_items = graph_adapter.apply_memory_decay(advanced_decay=True)

        # Check that some items have decayed
        assert len(volatile_items) > 0

        # Check that we can still retrieve the task
        task_items = graph_adapter.search({"type": "TASK"})
        assert len(task_items) > 0

    def test_query_edrr_phases_from_graph(self, coordinator, graph_adapter, sample_task):
        """Test querying EDRR phases from the graph memory."""
        # Start the EDRR cycle
        coordinator.start_cycle(sample_task)

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            coordinator.progress_to_phase(phase)

        # Query items for each phase
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            phase_items = graph_adapter.search({"edrr_phase": phase.name})
            assert len(phase_items) > 0

    def test_relationships_across_edrr_phases(self, coordinator, graph_adapter, sample_task):
        """Test relationships between items across EDRR phases."""
        # Start the EDRR cycle
        coordinator.start_cycle(sample_task)

        # Store items with relationships across phases
        expand_item = MemoryItem(
            id="expand-item",
            content="Expand phase item",
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "EXPAND", "cycle_id": coordinator.cycle_id}
        )
        graph_adapter.store(expand_item)

        differentiate_item = MemoryItem(
            id="differentiate-item",
            content="Differentiate phase item",
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "DIFFERENTIATE", "cycle_id": coordinator.cycle_id, "related_to": "expand-item"}
        )
        graph_adapter.store(differentiate_item)

        refine_item = MemoryItem(
            id="refine-item",
            content="Refine phase item",
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "REFINE", "cycle_id": coordinator.cycle_id, "related_to": "differentiate-item"}
        )
        graph_adapter.store(refine_item)

        retrospect_item = MemoryItem(
            id="retrospect-item",
            content="Retrospect phase item",
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "RETROSPECT", "cycle_id": coordinator.cycle_id, "related_to": "refine-item"}
        )
        graph_adapter.store(retrospect_item)

        # Query related items for the expand item
        related_to_expand = graph_adapter.query_related_items("expand-item")
        assert len(related_to_expand) == 1
        assert related_to_expand[0].id == "differentiate-item"

        # Get all relationships
        relationships = graph_adapter.get_all_relationships()
        assert "expand-item" in relationships
        assert "differentiate-item" in relationships
        assert "refine-item" in relationships
        assert "retrospect-item" in relationships
