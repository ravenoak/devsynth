from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    mm.store_with_edrr_phase.return_value = None
    wsde = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde,
        code_analyzer=ca,
        ast_transformer=ast,
        prompt_manager=pm,
        documentation_manager=dm,
    )


def test_progress_to_phase_auto_recursion(coordinator):
    coordinator.task = {"description": "t"}
    coordinator.cycle_id = "cid"
    coordinator.auto_phase_transitions = True
    phase_iter = iter([Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT])
    with (
        patch.object(
            coordinator, "_execute_expand_phase", return_value={"phase_complete": True}
        ) as ex,
        patch.object(
            coordinator,
            "_execute_differentiate_phase",
            return_value={"phase_complete": True},
        ) as diff,
        patch.object(
            coordinator, "_execute_refine_phase", return_value={"phase_complete": True}
        ) as ref,
        patch.object(
            coordinator,
            "_execute_retrospect_phase",
            return_value={"phase_complete": True},
        ) as ret,
        patch.object(
            coordinator,
            "_decide_next_phase",
            side_effect=lambda: next(phase_iter, None),
        ),
    ):
        coordinator.progress_to_phase(Phase.EXPAND)
    assert coordinator.current_phase == Phase.RETROSPECT
    assert ex.called and diff.called and ref.called and ret.called


def test_should_terminate_recursion_granularity(coordinator):
    """Recursion stops when granularity is below the threshold."""
    task = {"granularity_score": 0.1}
    assert coordinator.should_terminate_recursion(task) is True


def test_should_terminate_recursion_cost_benefit(coordinator):
    """Recursion stops when cost outweighs benefit."""
    task = {"cost_score": 0.8, "benefit_score": 0.1}
    assert coordinator.should_terminate_recursion(task) is True


def test_should_terminate_recursion_quality_threshold(coordinator):
    """Recursion stops when quality already meets the threshold."""
    task = {"quality_score": 0.95}
    assert coordinator.should_terminate_recursion(task) is True


def test_should_terminate_recursion_resource_limit(coordinator):
    """Recursion stops when resource usage is too high."""
    task = {"resource_usage": 0.9}
    assert coordinator.should_terminate_recursion(task) is True


@pytest.mark.parametrize(
    "task,expected",
    [({"human_override": "terminate"}, True), ({"human_override": "continue"}, False)],
)
def test_should_terminate_recursion_human_override(coordinator, task, expected):
    """Human override explicitly controls termination."""
    assert coordinator.should_terminate_recursion(task) is expected


def test_should_terminate_recursion_no_factors(coordinator):
    """Recursion continues when no delimiting factors trigger."""
    task = {
        "granularity_score": 0.8,
        "cost_score": 0.1,
        "benefit_score": 0.9,
        "quality_score": 0.1,
        "resource_usage": 0.1,
    }
    assert coordinator.should_terminate_recursion(task) is False
