from unittest.mock import MagicMock

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
    wsde = MagicMock()
    wsde.process.return_value = {"quality_score": 0.5}
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    coord = EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde,
        code_analyzer=ca,
        ast_transformer=ast,
        prompt_manager=pm,
        documentation_manager=dm,
    )
    coord.cycle_id = "cid"
    return coord


@pytest.mark.medium
def test_execute_micro_cycle_uses_dialectical_reasoning(coordinator):
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning = MagicMock(
        return_value={"quality_score": 0.8}
    )
    result = coordinator._execute_micro_cycle(Phase.EXPAND, 1)
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning.assert_called_once()
    assert result["quality_score"] == 0.8


@pytest.mark.medium
def test_execute_micro_cycle_handles_dialectical_errors(coordinator):
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning = MagicMock(
        side_effect=RuntimeError("dialectical failed")
    )
    result = coordinator._execute_micro_cycle(Phase.EXPAND, 2)
    assert result["quality_score"] == 0.5
    assert coordinator.performance_metrics["dialectical_failures"][0]["iteration"] == 2


def test_assess_result_quality_from_score(coordinator):
    assert coordinator._assess_result_quality({"quality_score": "0.7"}) == 0.7


@pytest.mark.medium
def test_assess_result_quality_handles_error(coordinator):
    value = coordinator._assess_result_quality({"quality_score": "bad"})
    assert value == pytest.approx(min(1.0, len(str({"quality_score": "bad"})) / 1000))
