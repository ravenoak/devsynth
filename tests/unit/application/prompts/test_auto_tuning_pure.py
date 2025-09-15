"""Pure PromptVariant helper behaviour."""

from __future__ import annotations

import pytest

from devsynth.application.prompts.auto_tuning import PromptVariant

pytestmark = pytest.mark.fast


def test_success_rate_and_average_feedback_are_computed_from_state() -> None:
    """Derive success metrics purely from stored counters.

    ReqID: N/A
    """

    variant = PromptVariant("template", variant_id="v1")
    variant.usage_count = 8
    variant.success_count = 6
    variant.feedback_scores = [0.25, 0.75]

    assert variant.success_rate == pytest.approx(0.75)
    assert variant.average_feedback_score == pytest.approx(0.5)


def test_performance_score_combines_success_and_feedback() -> None:
    """The weighted score blends success rate and feedback average.

    ReqID: N/A
    """

    variant = PromptVariant("template", variant_id="v2")
    variant.usage_count = 4
    variant.success_count = 3
    variant.feedback_scores = [0.9, 0.6, 0.3]

    expected = 0.7 * (3 / 4) + 0.3 * ((0.9 + 0.6 + 0.3) / 3)
    assert variant.performance_score == pytest.approx(expected)


def test_round_trip_serialisation_preserves_variant_fields() -> None:
    """``to_dict`` followed by ``from_dict`` yields an equivalent instance.

    ReqID: N/A
    """

    variant = PromptVariant("template", variant_id="variant-x")
    variant.usage_count = 5
    variant.success_count = 4
    variant.failure_count = 1
    variant.feedback_scores = [1.0, 0.4]
    variant.last_used = "2024-01-01T00:00:00"

    data = variant.to_dict()
    recreated = PromptVariant.from_dict(data)

    assert recreated.variant_id == "variant-x"
    assert recreated.template == "template"
    assert recreated.usage_count == 5
    assert recreated.success_count == 4
    assert recreated.failure_count == 1
    assert recreated.feedback_scores == [1.0, 0.4]
    assert recreated.last_used == "2024-01-01T00:00:00"
