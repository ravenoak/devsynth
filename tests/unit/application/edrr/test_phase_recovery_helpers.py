from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.edrr_phase_transitions import MetricType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
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
def test_recovery_registration_and_threshold_config(base_dependencies):
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EnhancedEDRRCoordinator(mm, team, ca, ast, pm, dm)

    def hook(metrics):
        metrics[MetricType.QUALITY.value] = 1.0
        return {"recovered": True}

    coord.register_phase_recovery_hook(Phase.EXPAND, hook)
    coord.configure_phase_thresholds(Phase.EXPAND, {MetricType.QUALITY.value: 0.9})
    coord.phase_metrics.start_phase(Phase.EXPAND)
    coord.phase_metrics.end_phase(
        Phase.EXPAND,
        {
            MetricType.QUALITY.value: 0.2,
            MetricType.COMPLETENESS.value: 1.0,
            MetricType.CONSISTENCY.value: 1.0,
            MetricType.CONFLICTS.value: 0,
        },
    )
    should_transition, reasons = coord.phase_metrics.should_transition(Phase.EXPAND)
    assert should_transition is True
    assert reasons["recovery"] == "metrics recovered"
    assert (
        coord.phase_metrics.get_thresholds(Phase.EXPAND)[MetricType.QUALITY.value]
        == 0.9
    )


@pytest.mark.medium
def test_micro_cycle_recovery_auto_progress(base_dependencies):
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EnhancedEDRRCoordinator(mm, team, ca, ast, pm, dm)
    coord.start_cycle({"description": "macro"})
    micro = coord.create_micro_cycle({"description": "micro"}, Phase.EXPAND)

    def hook(metrics):
        metrics[MetricType.QUALITY.value] = 1.0
        return {"recovered": True}

    micro.register_phase_recovery_hook(Phase.EXPAND, hook)
    micro.phase_metrics.end_phase(
        Phase.EXPAND,
        {
            MetricType.QUALITY.value: 0.2,
            MetricType.COMPLETENESS.value: 1.0,
            MetricType.CONSISTENCY.value: 1.0,
            MetricType.CONFLICTS.value: 0,
        },
    )
    micro._enhanced_maybe_auto_progress()
    assert micro.current_phase == Phase.DIFFERENTIATE
