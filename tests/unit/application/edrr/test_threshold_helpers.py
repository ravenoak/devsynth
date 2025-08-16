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
def base_dependencies():
    mm = MagicMock(spec=MemoryManager)
    team = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    return mm, team, ca, ast, pm, dm


@pytest.mark.medium
def test_assess_phase_quality_uses_config_threshold(base_dependencies):
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"phase_transitions": {"quality_thresholds": {"expand": 0.6}}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    coord.results[Phase.EXPAND.name] = {}
    with patch.object(EDRRCoordinator, "_assess_result_quality", return_value=0.5):
        assessment = coord._assess_phase_quality(Phase.EXPAND)
    assert assessment["can_progress"] is False


@pytest.mark.medium
def test_micro_cycle_config_sanitization(base_dependencies):
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"micro_cycles": {"max_iterations": 100, "quality_threshold": 2.0}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    with patch.object(EDRRCoordinator, "_assess_result_quality", return_value=0.1):
        # iteration 0 allowed, iteration 1 stops due to sanitized max_iterations=1
        assert coord._should_continue_micro_cycles(Phase.EXPAND, 0, {}) is True
        assert coord._should_continue_micro_cycles(Phase.EXPAND, 1, {}) is False
