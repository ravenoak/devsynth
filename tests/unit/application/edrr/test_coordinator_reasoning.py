import logging
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


@pytest.fixture
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    wsde_team = MagicMock()
    coord = EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde_team,
        code_analyzer=MagicMock(spec=CodeAnalyzer),
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
    )
    coord.cycle_id = "cid"
    return coord


def test_apply_dialectical_reasoning_success(coordinator):
    final = {"status": "completed", "synthesis": "done"}
    with patch(
        "devsynth.application.edrr.coordinator.reasoning_loop",
        return_value=[{"synthesis": "next"}, final],
    ) as rl:
        result = coordinator.apply_dialectical_reasoning(
            {"solution": "initial"}, MagicMock()
        )
    rl.assert_called_once()
    coordinator.memory_manager.flush_updates.assert_called_once()
    assert result == final


def test_apply_dialectical_reasoning_consensus_failure(coordinator, caplog):
    with patch("devsynth.application.edrr.coordinator.reasoning_loop", return_value=[]):
        with caplog.at_level(logging.WARNING):
            result = coordinator.apply_dialectical_reasoning(
                {"solution": "initial"}, MagicMock()
            )
    assert result == {}
    assert coordinator.performance_metrics["consensus_failures"]
    assert "Consensus failure" in caplog.text
