import json
import os
import shutil
import tempfile
from typing import Any, Dict
from collections.abc import Generator
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
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test resources.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Yield the directory path to the test
    yield temp_dir

    # Teardown: Remove the temporary directory and all its contents
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def memory_manager() -> Generator[MagicMock, None, None]:
    """Return a mock memory manager that stores items in a dict.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
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

    # Yield the mock to the test
    yield mock

    # Teardown: Clear stored items to prevent state leakage between tests
    mock.stored_items.clear()


@pytest.fixture
def wsde_team() -> Generator[MagicMock, None, None]:
    """Return a mock WSDE team.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
    mock = MagicMock(spec=WSDETeam)
    mock.generate_diverse_ideas.return_value = []
    mock.create_comparison_matrix.return_value = {}
    mock.evaluate_options.return_value = []
    mock.analyze_trade_offs.return_value = []
    mock.formulate_decision_criteria.return_value = {}
    mock.select_best_option.return_value = {}
    mock.elaborate_details.return_value = []
    mock.create_implementation_plan.return_value = []
    mock.optimize_implementation.return_value = {}
    mock.perform_quality_assurance.return_value = {}
    mock.extract_learnings.return_value = []
    mock.recognize_patterns.return_value = []
    mock.integrate_knowledge.return_value = {}
    mock.generate_improvement_suggestions.return_value = []

    # Yield the mock to the test
    yield mock

    # Teardown: Reset the mock to prevent state leakage between tests
    mock.reset_mock()


@pytest.fixture
def code_analyzer() -> Generator[MagicMock, None, None]:
    """Return a mock code analyzer.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
    mock = MagicMock(spec=CodeAnalyzer)
    mock.analyze_project_structure.return_value = {}

    # Yield the mock to the test
    yield mock

    # Teardown: Reset the mock to prevent state leakage between tests
    mock.reset_mock()


@pytest.fixture
def ast_transformer() -> Generator[MagicMock, None, None]:
    """Return a mock AST transformer.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
    mock = MagicMock(spec=AstTransformer)

    # Yield the mock to the test
    yield mock

    # Teardown: Reset the mock to prevent state leakage between tests
    mock.reset_mock()


@pytest.fixture
def prompt_manager() -> Generator[MagicMock, None, None]:
    """Return a mock prompt manager.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
    mock = MagicMock(spec=PromptManager)

    # Yield the mock to the test
    yield mock

    # Teardown: Reset the mock to prevent state leakage between tests
    mock.reset_mock()


@pytest.fixture
def documentation_manager() -> Generator[MagicMock, None, None]:
    """Return a mock documentation manager.

    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create the mock
    mock = MagicMock(spec=DocumentationManager)

    # Yield the mock to the test
    yield mock

    # Teardown: Reset the mock to prevent state leakage between tests
    mock.reset_mock()


@pytest.fixture
def coordinator(
    temp_dir,
    memory_manager,
    wsde_team,
    code_analyzer,
    ast_transformer,
    prompt_manager,
    documentation_manager,
) -> Generator[EDRRCoordinator, None, None]:
    """Return an EDRR coordinator with mock dependencies.

    This fixture uses a generator pattern to provide teardown functionality.
    It also uses the temp_dir fixture to ensure any files created by the coordinator
    are isolated and cleaned up after the test.
    """
    # Setup: Create the coordinator
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
        workspace_dir=temp_dir,  # Use temporary directory for workspace
    )

    # Yield the coordinator to the test
    yield coordinator

    # Teardown: Clean up any resources created by the coordinator
    if hasattr(coordinator, "cleanup") and callable(coordinator.cleanup):
        coordinator.cleanup()

    # Reset the coordinator's state to prevent leakage between tests
    coordinator.child_cycles = {}
    if hasattr(coordinator, "results"):
        coordinator.results.clear()


@pytest.mark.medium
def test_recursion_depth_exceeded_succeeds(coordinator):
    """Test that recursion depth exceeded succeeds.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "root"})
    current = coordinator
    for i in range(coordinator.max_recursion_depth):
        current = current.create_micro_cycle(
            {"description": f"level {i}"}, Phase.EXPAND
        )
    with pytest.raises(EDRRCoordinatorError):
        current.create_micro_cycle({"description": "too deep"}, Phase.EXPAND)


@pytest.mark.medium
def test_recursion_depth_increments_succeeds(coordinator):
    """Micro cycles should increment recursion depth until the limit.

    ReqID: N/A"""
    coordinator.auto_phase_transitions = False
    coordinator.start_cycle({"description": "root"})
    micro1 = coordinator.create_micro_cycle({"description": "level1"}, Phase.EXPAND)
    assert micro1.recursion_depth == 1
    micro2 = micro1.create_micro_cycle({"description": "level2"}, Phase.EXPAND)
    assert micro2.recursion_depth == 2
    micro3 = micro2.create_micro_cycle({"description": "level3"}, Phase.EXPAND)
    assert micro3.recursion_depth == coordinator.max_recursion_depth


@pytest.mark.medium
def test_abort_when_should_terminate_succeeds(coordinator):
    """Test that abort when should terminate succeeds.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "macro"})
    with patch.object(
        coordinator, "should_terminate_recursion", return_value=(True, "test reason")
    ):
        with pytest.raises(EDRRCoordinatorError):
            coordinator.create_micro_cycle({"description": "micro"}, Phase.EXPAND)
    assert not coordinator.child_cycles


@pytest.mark.medium
def test_store_metadata_and_results_succeeds(coordinator, memory_manager):
    """Test that store metadata and results succeeds.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "macro"})
    micro_task = {"description": "micro"}
    micro = coordinator.create_micro_cycle(micro_task, Phase.EXPAND)
    stored = memory_manager.stored_items.get("MICRO_CYCLE")
    assert stored["item"]["micro_cycle_id"] == micro.cycle_id
    assert stored["item"]["task"] == micro_task
    assert stored["metadata"]["cycle_id"] == coordinator.cycle_id
    assert stored["metadata"]["recursion_depth"] == 1
    parent_results = coordinator.results[Phase.EXPAND.name]["micro_cycle_results"][
        micro.cycle_id
    ]
    assert parent_results["task"] == micro_task
    for key, value in micro.results.items():
        assert parent_results[key] == value


@pytest.mark.medium
def test_parent_aggregates_after_micro_phase_succeeds(coordinator):
    """Parent aggregated results should refresh when a micro cycle progresses.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "macro"})
    micro = coordinator.create_micro_cycle({"description": "micro"}, Phase.EXPAND)
    with patch.object(
        micro, "_execute_differentiate_phase", return_value={"done": True}
    ):
        micro.progress_to_phase(Phase.DIFFERENTIATE)
    aggregated = coordinator.results.get("AGGREGATED", {})
    assert "child_cycles" in aggregated
    assert "individual_cycles" in aggregated["child_cycles"]
    assert micro.cycle_id in aggregated["child_cycles"]["individual_cycles"]


@pytest.mark.medium
def test_create_micro_cycle_from_manifest_dict_succeeds(coordinator):
    """Test that create micro cycle from manifest dict succeeds.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "root"})
    task = {"manifest": {"task": {"description": "micro"}}}
    with patch.object(EDRRCoordinator, "start_cycle_from_manifest") as start_mock:
        micro = coordinator.create_micro_cycle(task, Phase.EXPAND)
    start_mock.assert_called_once_with(
        json.dumps({"task": {"description": "micro"}}), is_file=False
    )
    assert micro.parent_cycle_id == coordinator.cycle_id
