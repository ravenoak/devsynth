import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.edrr.coordinator import EDRRCoordinator
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
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    team = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    coord = EDRRCoordinator(mm, team, ca, ast, pm, dm)
    coord.cycle_id = "cid"
    return coord


def test_micro_cycle_hooks_invoked(coordinator):
    events = []

    def start(info):
        events.append(("start", info["iteration"]))

    def end(info):
        events.append(("end", info["iteration"]))

    coordinator.register_micro_cycle_hook("start", start)
    coordinator.register_micro_cycle_hook("end", end)

    with patch.object(EDRRCoordinator, "start_cycle", return_value=None):
        coordinator.create_micro_cycle({"description": "sub"}, Phase.EXPAND)

    assert ("start", 0) in events
    assert ("end", 0) in events
