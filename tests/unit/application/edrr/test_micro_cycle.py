import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def memory_manager():
    """Return a mock memory manager that stores items in a dict."""
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
    return mock


@pytest.fixture
def code_analyzer():
    mock = MagicMock(spec=CodeAnalyzer)
    mock.analyze_project_structure.return_value = {}
    return mock


@pytest.fixture
def ast_transformer():
    return MagicMock(spec=AstTransformer)


@pytest.fixture
def prompt_manager():
    return MagicMock(spec=PromptManager)


@pytest.fixture
def documentation_manager():
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
    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
    )


def test_recursion_depth_exceeded(coordinator):
    coordinator.start_cycle({"description": "root"})
    current = coordinator
    for i in range(coordinator.max_recursion_depth):
        current = current.create_micro_cycle(
            {"description": f"level {i}"}, Phase.EXPAND
        )
    with pytest.raises(EDRRCoordinatorError):
        current.create_micro_cycle({"description": "too deep"}, Phase.EXPAND)


def test_abort_when_should_terminate(coordinator):
    coordinator.start_cycle({"description": "macro"})
    with patch.object(coordinator, "should_terminate_recursion", return_value=True):
        with pytest.raises(EDRRCoordinatorError):
            coordinator.create_micro_cycle({"description": "micro"}, Phase.EXPAND)
    assert not coordinator.child_cycles


def test_store_metadata_and_results(coordinator, memory_manager):
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
