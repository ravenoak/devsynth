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
from devsynth.domain.models.wsde_facade import WSDETeam
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


@pytest.mark.medium
def test_progress_to_phase_auto_recursion_succeeds(coordinator):
    """Test that progress to phase auto recursion succeeds.

    ReqID: N/A"""
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


@pytest.mark.medium
def test_should_terminate_recursion_granularity_succeeds(coordinator):
    """Recursion stops when granularity is below the threshold.

    ReqID: N/A"""
    task = {"granularity_score": 0.1}
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is True
    assert result[1] == "granularity threshold"


@pytest.mark.medium
def test_should_terminate_recursion_cost_benefit_succeeds(coordinator):
    """Recursion stops when cost outweighs benefit.

    ReqID: N/A"""
    task = {"cost_score": 0.8, "benefit_score": 0.1}
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is True
    assert result[1] == "cost-benefit analysis"


@pytest.mark.medium
def test_should_terminate_recursion_quality_threshold_succeeds(coordinator):
    """Recursion stops when quality already meets the threshold.

    ReqID: N/A"""
    task = {"quality_score": 0.95}
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is True
    assert result[1] == "quality threshold"


@pytest.mark.medium
def test_should_terminate_recursion_resource_limit_succeeds(coordinator):
    """Recursion stops when resource usage is too high.

    ReqID: N/A"""
    task = {"resource_usage": 0.9}
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is True
    assert result[1] == "resource limit"


@pytest.mark.parametrize(
    "task,expected,reason",
    [
        ({"human_override": "terminate"}, True, "human override"),
        ({"human_override": "continue"}, False, None),
    ],
)
@pytest.mark.medium
def test_should_terminate_recursion_human_override_succeeds(
    coordinator, task, expected, reason
):
    """Human override explicitly controls termination.

    ReqID: N/A"""
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is expected
    assert result[1] == reason


@pytest.mark.medium
def test_should_terminate_recursion_no_factors_succeeds(coordinator):
    """Recursion continues when no delimiting factors trigger.

    ReqID: N/A"""
    task = {
        "granularity_score": 0.8,
        "cost_score": 0.1,
        "benefit_score": 0.9,
        "quality_score": 0.1,
        "resource_usage": 0.1,
    }
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is False
    assert result[1] is None


@pytest.mark.medium
def test_should_terminate_recursion_at_thresholds_succeeds(coordinator):
    """Exactly meeting thresholds should not trigger termination.

    ReqID: N/A"""
    task = {
        "granularity_score": coordinator.DEFAULT_GRANULARITY_THRESHOLD,
        "cost_score": coordinator.DEFAULT_COST_BENEFIT_RATIO,
        "benefit_score": 1.0,
    }
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is False
    assert result[1] is None


@pytest.mark.medium
def test_should_terminate_recursion_combined_factors_fails(coordinator):
    """Multiple failing factors still trigger termination.

    ReqID: N/A"""
    task = {
        "granularity_score": coordinator.DEFAULT_GRANULARITY_THRESHOLD / 2,
        "cost_score": 0.6,
        "benefit_score": 0.2,
    }
    result = coordinator.should_terminate_recursion(task)
    assert result[0] is True
    assert result[1] == "granularity threshold"
