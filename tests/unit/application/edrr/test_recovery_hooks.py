from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
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
def test_recovery_hook_success_injects_results_and_sets_recovered(base_dependencies):
    """A registered phase-specific recovery hook can recover and inject results.

    This validates the failure recovery hooks requirement in the orchestration layer.
    """
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config={})
    phase = Phase.EXPAND

    def recover_hook(**kwargs):
        # kwargs: error, phase, coordinator
        return {"recovered": True, "results": {"injected": True, "value": 42}}

    coord.register_recovery_hook(phase, recover_hook)

    info = coord._attempt_recovery(RuntimeError("boom"), phase)

    assert info.get("recovered") is True
    # Results injected by hook are merged into coordinator results for the phase
    assert coord.results.get(phase.name, {}).get("injected") is True
    assert coord.results.get(phase.name, {}).get("value") == 42


@pytest.mark.medium
def test_recovery_retry_when_hooks_do_not_recover(base_dependencies):
    """When hooks do not recover, coordinator retries executing the phase once.

    Ensures the fallback recovery path is exercised and results are merged.
    """
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config={})
    phase = Phase.REFINE

    def non_recovering_hook(**kwargs):
        return {"recovered": False, "note": "no-op"}

    coord.register_recovery_hook(phase, non_recovering_hook)

    with patch.object(
        EDRRCoordinator, "_execute_phase", return_value={"foo": "bar"}
    ) as exec_phase:
        info = coord._attempt_recovery(RuntimeError("fail"), phase)

    exec_phase.assert_called_once_with(phase)
    assert info.get("recovered") is True
    assert info.get("strategy") == "retry"
    assert coord.results.get(phase.name, {}).get("foo") == "bar"


@pytest.mark.medium
def test_recovery_hooks_ignores_hook_exceptions_and_continues(base_dependencies):
    """Hook exceptions are handled defensively; next hooks still run and can recover."""
    mm, team, ca, ast, pm, dm = base_dependencies
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm, config={})
    phase = Phase.DIFFERENTIATE

    def bad_hook(**kwargs):
        raise ValueError("hook exploded")

    def good_hook(**kwargs):
        return {"recovered": True, "results": {"ok": 1}}

    # Register a global bad hook and a phase-specific good hook
    coord.register_recovery_hook(None, bad_hook)
    coord.register_recovery_hook(phase, good_hook)

    info = coord._attempt_recovery(RuntimeError("err"), phase)

    assert info.get("recovered") is True
    assert coord.results.get(phase.name, {}).get("ok") == 1
