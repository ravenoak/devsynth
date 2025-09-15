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
    mm.store_with_edrr_phase.return_value = "id"
    mm.retrieve_with_edrr_phase.return_value = {}
    mm.retrieve_historical_patterns.return_value = []
    mm.retrieve_relevant_knowledge.return_value = []
    team = MagicMock()
    team.process.return_value = {"quality_score": 0.6}
    team.apply_enhanced_dialectical_reasoning.side_effect = lambda task, res: res
    coord = EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=MagicMock(spec=CodeAnalyzer),
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=True,
    )
    coord.config = {
        "edrr": {"micro_cycles": {"max_iterations": 2, "quality_threshold": 0.8}}
    }
    return coord


@pytest.mark.medium
def test_micro_cycle_iterations_until_threshold(coordinator):
    """Micro cycles repeat until quality threshold met.

    ReqID: N/A"""
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {"description": "task"}
    coordinator.cycle_id = "cid"
    with patch.object(
        coordinator, "_execute_expand_phase", return_value={"quality_score": 0.5}
    ):
        coordinator.wsde_team.process.side_effect = [
            {"quality_score": 0.6},
            {"quality_score": 0.9},
        ]
        results = coordinator.execute_current_phase()
    assert coordinator.wsde_team.process.call_count == 2
    phase_results = coordinator.results[Phase.EXPAND.name]
    assert len(phase_results["micro_cycle_iterations"]) == 2
    assert phase_results["aggregated_results"]["quality_score"] == 0.9
    assert results["quality_score"] == 0.9


@pytest.mark.medium
def test_phase_execution_recovery_hook(coordinator):
    """Recovery hook executed on phase failure.

    ReqID: N/A"""
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {"description": "task"}
    coordinator.cycle_id = "cid"
    with patch.object(
        coordinator, "_execute_expand_phase", side_effect=RuntimeError("boom")
    ):
        with patch.object(
            coordinator, "_attempt_recovery", return_value={"recovered": True}
        ) as rec:
            results = coordinator.execute_current_phase()
    rec.assert_called_once()
    assert results.get("recovery_info")


@pytest.mark.medium
def test_micro_cycle_respects_max_iterations(coordinator):
    """Micro cycles stop at max iteration count.

    ReqID: N/A"""
    coordinator.config["edrr"]["micro_cycles"]["max_iterations"] = 1
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {"description": "task"}
    coordinator.cycle_id = "cid"
    with patch.object(
        coordinator, "_execute_expand_phase", return_value={"quality_score": 0.1}
    ):
        coordinator.wsde_team.process.return_value = {"quality_score": 0.2}
        results = coordinator.execute_current_phase()
    assert coordinator.wsde_team.process.call_count == 1
    phase_results = coordinator.results[Phase.EXPAND.name]
    assert len(phase_results["micro_cycle_iterations"]) == 1
    assert phase_results["aggregated_results"]["quality_score"] == 0.2
    assert results["quality_score"] == 0.2


@pytest.mark.fast
def test_run_micro_cycles_stops_after_threshold():
    """Micro cycles stop when quality threshold is reached.

    ReqID: N/A"""
    coordinator = EDRRCoordinator(
        memory_manager=MagicMock(spec=MemoryManager),
        wsde_team=MagicMock(spec=WSDETeam),
        code_analyzer=MagicMock(spec=CodeAnalyzer),
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
    )

    with patch.object(coordinator, "_get_micro_cycle_config", return_value=(3, 0.8)):
        with patch.object(
            coordinator, "_assess_result_quality", side_effect=[0.5, 0.9]
        ):
            with patch.object(
                coordinator,
                "_execute_micro_cycle",
                return_value={"quality_score": 0.9},
            ) as exec_micro:
                with patch.object(
                    coordinator,
                    "_aggregate_micro_cycle_results",
                    return_value={"aggregated_results": {"quality_score": 0.9}},
                ):
                    coordinator._run_micro_cycles(Phase.EXPAND, {"quality_score": 0.5})

    exec_micro.assert_called_once()
