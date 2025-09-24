"""High-fidelity simulations for EDRR coordinator recursion behaviors.

These tests align with the scenarios captured in
``tests/behavior/features/recursive_edrr_coordinator.feature`` to keep
macro/micro expectations deterministic while exercising the richer
orchestration paths implemented in ``core.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture(scope="module")
def recursive_feature_tasks() -> dict[str, Any]:
    """Parse the recursive coordinator feature to keep task labels in sync."""

    feature_path = Path("tests/behavior/features/recursive_edrr_coordinator.feature")
    text = feature_path.read_text(encoding="utf-8")

    macro_match = re.search(
        r'start the EDRR cycle with a task to "(?P<task>[^"]+)"', text
    )
    if not macro_match:
        raise AssertionError("Recursive EDRR feature no longer defines a macro task")

    micro_matches = re.findall(
        r'create a micro-EDRR cycle for "(?P<task>[^"]+)" within the "Expand" phase(?: of the "[^"]+" cycle)?',
        text,
    )
    if len(micro_matches) < 4:
        raise AssertionError(
            "Recursive EDRR feature must enumerate the level 0–3 micro-cycle tasks"
        )

    return {
        "macro_task": macro_match.group("task"),
        "micro_tasks": micro_matches,
    }


@pytest.fixture
def memory_manager() -> MagicMock:
    """Provide a memory manager stub that records persistence side effects."""

    manager = MagicMock(spec=MemoryManager)
    manager.store_with_edrr_phase.return_value = "mem-001"
    manager.flush_updates.return_value = None
    manager.register_sync_hook.return_value = None
    manager.retrieve_with_edrr_phase.return_value = {}
    return manager


@pytest.fixture
def wsde_team() -> MagicMock:
    """Provide a WSDE team stub with the hooks used during transitions."""

    team = MagicMock(spec=WSDETeam)
    team.rotate_primus.return_value = None
    team.assign_roles_for_phase.return_value = None
    team.get_role_map.return_value = {"Primus": "Explorer"}
    team.elaborate_details.return_value = []
    team.generate_diverse_ideas.return_value = []
    team.evaluate_options.return_value = []
    team.select_best_option.return_value = {}
    team.create_implementation_plan.return_value = []
    team.optimize_implementation.return_value = {}
    team.perform_quality_assurance.return_value = {}
    team.extract_learnings.return_value = []
    team.apply_enhanced_dialectical_reasoning.side_effect = (
        lambda task, results: results
    )
    return team


@pytest.fixture
def code_analyzer() -> MagicMock:
    return MagicMock(spec=CodeAnalyzer)


@pytest.fixture
def ast_transformer() -> MagicMock:
    return MagicMock(spec=AstTransformer)


@pytest.fixture
def prompt_manager() -> MagicMock:
    return MagicMock(spec=PromptManager)


@pytest.fixture
def documentation_manager() -> MagicMock:
    return MagicMock(spec=DocumentationManager)


@pytest.fixture
def coordinator_config() -> dict[str, Any]:
    """Deterministic thresholds for the recursive simulations."""

    return {
        "features": {"automatic_phase_transitions": True},
        "edrr": {
            "max_recursion_depth": 3,
            "phase_transition": {"timeout": 60},
            "phase_transitions": {
                "quality_thresholds": {
                    "expand": 0.9,
                    "differentiate": 0.9,
                    "refine": 0.9,
                }
            },
            "micro_cycles": {"max_iterations": 2, "quality_threshold": 0.8},
        },
    }


@pytest.fixture
def coordinator(
    memory_manager: MagicMock,
    wsde_team: MagicMock,
    code_analyzer: MagicMock,
    ast_transformer: MagicMock,
    prompt_manager: MagicMock,
    documentation_manager: MagicMock,
    coordinator_config: dict[str, Any],
) -> EDRRCoordinator:
    """Instantiate a coordinator with enhanced logging for traceability."""

    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
        config=coordinator_config,
    )


@pytest.mark.medium
def test_phase_transitions_follow_recursive_feature(
    recursive_feature_tasks: dict[str, Any],
    coordinator: EDRRCoordinator,
    wsde_team: MagicMock,
) -> None:
    """Auto transitions honour BDD macro/micro expectations up to Refine."""

    macro_task = {"description": recursive_feature_tasks["macro_task"]}

    with patch(
        "devsynth.application.edrr.coordinator.phase_management.flush_memory_queue",
        return_value=None,
    ) as flush_memory_queue:
        coordinator.start_cycle(macro_task)

        assert coordinator.current_phase == Phase.EXPAND

        micro_task = {"description": recursive_feature_tasks["micro_tasks"][0]}
        micro_cycle = coordinator.create_micro_cycle(micro_task, Phase.EXPAND)

        assert micro_cycle.parent_cycle_id == coordinator.cycle_id
        assert micro_cycle.parent_phase == Phase.EXPAND
        assert micro_cycle.recursion_depth == 1
        assert micro_cycle in coordinator.child_cycles

        expand_results = coordinator.results[Phase.EXPAND.name]
        assert micro_cycle.cycle_id in expand_results["micro_cycle_results"]
        assert (
            expand_results["micro_cycle_results"][micro_cycle.cycle_id]["task"][
                "description"
            ]
            == recursive_feature_tasks["micro_tasks"][0]
        )

        coordinator.results[Phase.EXPAND.name].update(
            {"phase_complete": True, "quality_score": 0.96}
        )
        coordinator.results[Phase.DIFFERENTIATE.name] = {
            "phase_complete": True,
            "quality_score": 0.93,
        }
        coordinator.results[Phase.REFINE.name] = {
            "quality_score": 0.42,
            "details": ["needs polish"],
        }

        coordinator._maybe_auto_progress()

        assert coordinator.current_phase == Phase.REFINE
        refine_results = coordinator.results[Phase.REFINE.name]
        assert refine_results["additional_processing"] is True
        assert refine_results["quality_issues"][0]["threshold"] == pytest.approx(0.9)
        assert wsde_team.assign_roles_for_phase.call_count >= 3
        assert flush_memory_queue.called


@pytest.mark.medium
def test_recursion_depth_limit_matches_feature(
    recursive_feature_tasks: dict[str, Any],
    coordinator: EDRRCoordinator,
) -> None:
    """Depth 4 attempts raise the same guard documented in the feature."""

    with patch(
        "devsynth.application.edrr.coordinator.phase_management.flush_memory_queue",
        return_value=None,
    ):
        coordinator.start_cycle({"description": recursive_feature_tasks["macro_task"]})

        micro_cycle_level1 = coordinator.create_micro_cycle(
            {"description": recursive_feature_tasks["micro_tasks"][1]},
            Phase.EXPAND,
        )
        micro_cycle_level2 = micro_cycle_level1.create_micro_cycle(
            {"description": recursive_feature_tasks["micro_tasks"][2]},
            Phase.EXPAND,
        )
        micro_cycle_level3 = micro_cycle_level2.create_micro_cycle(
            {"description": recursive_feature_tasks["micro_tasks"][3]},
            Phase.EXPAND,
        )

        assert micro_cycle_level3.recursion_depth == coordinator.max_recursion_depth

        with pytest.raises(EDRRCoordinatorError) as excinfo:
            micro_cycle_level3.create_micro_cycle(
                {"description": "level 4 task"}, Phase.EXPAND
            )

        assert "Maximum recursion depth" in str(excinfo.value)
        assert micro_cycle_level3.child_cycles == []


@pytest.mark.medium
def test_failed_retry_reports_reason(
    coordinator: EDRRCoordinator,
) -> None:
    """Recovery surfaces retry failures with a diagnostic reason."""

    phase = Phase.RETROSPECT
    failure = RuntimeError("refine summary missing")

    with patch.object(
        EDRRCoordinator,
        "_execute_phase",
        side_effect=RuntimeError("retry attempt failed"),
    ):
        info = coordinator._attempt_recovery(failure, phase)

    assert info == {"recovered": False, "reason": "retry attempt failed"}
    assert coordinator.results.get(phase.name, {}) == {}
