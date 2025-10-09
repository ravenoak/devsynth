from unittest.mock import MagicMock

import pytest

from devsynth.application.edrr.coordinator import EDRRCoordinator


def _build_coord(config):
    return EDRRCoordinator(
        memory_manager=MagicMock(),
        wsde_team=MagicMock(),
        code_analyzer=MagicMock(),
        ast_transformer=MagicMock(),
        prompt_manager=MagicMock(),
        documentation_manager=MagicMock(),
        config=config,
    )


@pytest.mark.slow
def test_recursion_threshold_sanitization():
    """Ensure recursion thresholds fall back to safe defaults. ReqID: FR-40"""
    bad_config = {
        "edrr": {
            "max_recursion_depth": -5,
            "recursion": {"thresholds": {"granularity": -1, "quality": 2}},
        }
    }
    coord = _build_coord(bad_config)
    assert coord.max_recursion_depth == EDRRCoordinator.DEFAULT_MAX_RECURSION_DEPTH

    # Task should trigger granularity termination using default threshold 0.2
    terminate, reason = coord.should_terminate_recursion(
        {"granularity_score": 0.1, "quality_score": 0.95}
    )
    assert terminate is True
    assert reason == "granularity threshold"
