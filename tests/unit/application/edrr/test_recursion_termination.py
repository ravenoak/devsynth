"""Property-based tests for recursion termination in the EDRRCoordinator."""

from typing import Any, cast
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase
from tests._typing_utils import ensure_typed_decorator


def typed_given(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    return ensure_typed_decorator(
        cast(Callable[[Callable[..., Any]], Any], given(*args, **kwargs))
    )


def typed_settings(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    return ensure_typed_decorator(
        cast(Callable[[Callable[..., Any]], Any], settings(*args, **kwargs))
    )


@pytest.fixture
def coordinator_factory():
    """Create a coordinator factory with mocked dependencies."""

    def factory(max_depth: int = 3) -> EDRRCoordinator:
        memory_manager = MagicMock(spec=MemoryManager)
        wsde_team = MagicMock(spec=WSDETeam)
        code_analyzer = MagicMock(spec=CodeAnalyzer)
        ast_transformer = MagicMock(spec=AstTransformer)
        prompt_manager = MagicMock(spec=PromptManager)
        documentation_manager = MagicMock(spec=DocumentationManager)
        config = {"edrr": {"max_recursion_depth": max_depth}}
        return EDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=documentation_manager,
            enable_enhanced_logging=True,
            config=config,
        )

    return factory


@pytest.mark.property
@typed_given(max_depth=st.integers(min_value=1, max_value=3))
@typed_settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.fast
def test_micro_cycle_respects_depth_bounds(max_depth: int, coordinator_factory):
    """Ensure micro cycles stop at the configured recursion depth.

    ReqID: EDRR-RT-001"""
    coordinator = coordinator_factory(max_depth)
    with (
        patch.object(EDRRCoordinator, "start_cycle", lambda self, task: None),
        patch.object(EDRRCoordinator, "_aggregate_results", lambda self: None),
        patch.object(
            EDRRCoordinator, "_invoke_micro_cycle_hooks", lambda *_, **__: None
        ),
    ):
        coordinator.recursion_depth = max_depth - 1
        micro_cycle = coordinator.create_micro_cycle(
            {"description": "task"}, parent_phase=Phase.EXPAND
        )
        assert micro_cycle.recursion_depth == max_depth
        coordinator.recursion_depth = max_depth
        with pytest.raises(EDRRCoordinatorError):
            coordinator.create_micro_cycle(
                {"description": "task"}, parent_phase=Phase.EXPAND
            )


@pytest.mark.property
@typed_given(complexity_score=st.floats(min_value=0.71, max_value=1.0))
@typed_settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.fast
def test_complexity_threshold_triggers_termination(
    complexity_score: float, coordinator_factory
):
    """Verify recursion terminates when complexity exceeds the threshold.

    ReqID: EDRR-RT-002"""
    coordinator = coordinator_factory()
    task = {"description": "complex", "complexity_score": complexity_score}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert reason == "complexity threshold"
