from unittest.mock import patch

import pytest

from devsynth.application.edrr.edrr_phase_transitions import (
    MetricType,
    collect_phase_metrics,
)
from devsynth.methodology.base import Phase


@pytest.mark.fast
def test_collect_phase_metrics_uses_stubbed_helpers():
    """Quality and diversity metrics leverage helper functions.

    ReqID: N/A"""
    results = {"r1": {}, "r2": {}}

    with (
        patch(
            "devsynth.application.edrr.edrr_phase_transitions."
            "calculate_enhanced_quality_score",
            side_effect=[0.4, 0.6],
        ) as calc_score,
        patch(
            "devsynth.application.edrr.edrr_phase_transitions."
            "_calculate_idea_diversity",
            return_value=0.8,
        ) as idea_diversity,
    ):
        metrics = collect_phase_metrics(Phase.EXPAND, results)

    calc_score.assert_called()
    idea_diversity.assert_called_once()
    assert metrics[MetricType.QUALITY.value] == pytest.approx(0.5)
    assert metrics["idea_diversity"] == 0.8
