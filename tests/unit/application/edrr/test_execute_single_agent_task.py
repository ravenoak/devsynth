import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.domain.models.memory import MemoryType


@pytest.fixture
def coordinator():
    wsde_team = WSDETeam(name="team")
    agent = MagicMock()
    agent.process.return_value = {"result": "ok"}
    wsde_team.add_agent(agent)
    wsde_team.get_agent = MagicMock(return_value=agent)
    mm = MagicMock(spec=MemoryManager)
    mm.store_with_edrr_phase.return_value = "memid"
    return EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde_team,
        code_analyzer=MagicMock(spec=CodeAnalyzer),
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
    )


def test_execute_single_agent_task_stores_result_and_calls_agent(coordinator):
    with patch.object(
        coordinator, "_get_llm_response", return_value="done"
    ) as mock_llm:
        result = coordinator.execute_single_agent_task(
            task={"foo": "bar"},
            agent_name="agent",
            phase=Phase.ANALYSIS,
            llm_prompt="hi",
        )
    mock_llm.assert_called_once()
    coordinator.wsde_team.get_agent.assert_called_once_with("agent")
    coordinator.memory_manager.store_with_edrr_phase.assert_called()
    assert result["result"] == "ok"
    assert "quality_score" in result
