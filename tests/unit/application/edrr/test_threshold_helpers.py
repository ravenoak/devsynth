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
    """Issue: issues/recursive-edrr-coordinator.md."""
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"phase_transitions": {"quality_thresholds": {"expand": 0.6}}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    coord.results[Phase.EXPAND.name] = {}
    with patch.object(EDRRCoordinator, "_assess_result_quality", return_value=0.5):
        assessment = coord._assess_phase_quality(Phase.EXPAND)
    assert assessment["can_progress"] is False


@pytest.mark.medium
def test_micro_cycle_config_sanitization(base_dependencies):
    """Issue: issues/recursive-edrr-coordinator.md."""
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"micro_cycles": {"max_iterations": 100, "quality_threshold": 2.0}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    with patch.object(EDRRCoordinator, "_assess_result_quality", return_value=0.1):
        # iteration 0 allowed, iteration 1 stops due to sanitized max_iterations=1
        assert coord._should_continue_micro_cycles(Phase.EXPAND, 0, {}) is True
        assert coord._should_continue_micro_cycles(Phase.EXPAND, 1, {}) is False


@pytest.mark.fast
def test_sanitize_positive_int_handles_out_of_range():
    """Issue: issues/recursive-edrr-coordinator.md."""
    assert EDRRCoordinator._sanitize_positive_int(-5, 1) == 1
    assert EDRRCoordinator._sanitize_positive_int(12, 1, max_value=10) == 1
    assert EDRRCoordinator._sanitize_positive_int(3, 1) == 3


@pytest.mark.fast
def test_sanitize_threshold_clamps_invalid_values():
    """Issue: issues/recursive-edrr-coordinator.md."""
    assert EDRRCoordinator._sanitize_threshold(2.0, 0.7) == 0.7
    assert EDRRCoordinator._sanitize_threshold(-1.0, 0.7) == 0.7
    assert EDRRCoordinator._sanitize_threshold(0.8, 0.7) == 0.8


@pytest.mark.fast
def test_get_phase_quality_threshold_respects_config(base_dependencies):
    """Issue: issues/recursive-edrr-coordinator.md."""
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"phase_transitions": {"quality_thresholds": {"expand": 0.95}}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    assert coord._get_phase_quality_threshold(Phase.EXPAND) == pytest.approx(0.95)


@pytest.mark.fast
def test_get_phase_quality_threshold_returns_none_when_missing(base_dependencies):
    """Issue: issues/recursive-edrr-coordinator.md."""
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config={"edrr": {}})
    assert coord._get_phase_quality_threshold(Phase.DIFFERENTIATE) is None


@pytest.mark.fast
def test_get_micro_cycle_config_sanitizes_values(base_dependencies):
    """Issue: issues/recursive-edrr-coordinator.md."""
    mm, team, ca, ast, pm, dm = base_dependencies
    cfg = {"edrr": {"micro_cycles": {"max_iterations": 25, "quality_threshold": 2.5}}}
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config=cfg)
    max_iterations, quality_threshold = coord._get_micro_cycle_config()
    assert max_iterations == 1
    assert quality_threshold == pytest.approx(0.7)
