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
    team = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm)
    coord.cycle_id = "cid"
    coord.current_phase = Phase.EXPAND
    coord.task = {}
    return coord


@pytest.mark.medium
def test_recovery_hook_handles_error(coordinator):
    """Recovery hooks can intercept phase errors and provide results."""

    def hook(error, phase, coordinator):
        assert phase == Phase.EXPAND
        return {"recovered": True, "results": {"handled": True}}

    coordinator.register_recovery_hook(Phase.EXPAND, hook)

    with patch.object(EDRRCoordinator, "_execute_phase", side_effect=Exception("boom")):
        results = coordinator.execute_current_phase({})

    assert results["recovery_info"]["recovered"] is True
    assert results["handled"] is True


@pytest.mark.medium
def test_recovery_hook_fallback_retry(coordinator):
    """If hooks do not recover, coordinator retries the phase."""
    coordinator.register_recovery_hook(Phase.EXPAND, lambda **_: {"recovered": False})

    with patch.object(
        EDRRCoordinator,
        "_execute_expand_phase",
        side_effect=[Exception("boom"), {"value": 1}],
    ) as exec_mock:
        results = coordinator.execute_current_phase({})

    # First call fails, second call succeeds via retry
    assert exec_mock.call_count == 2
    assert results["recovery_info"]["recovered"] is True
    assert results["value"] == 1
