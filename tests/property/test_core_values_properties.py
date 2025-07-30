import pytest

pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st, assume

from devsynth.core.values import CoreValues, find_value_conflicts


@given(st.lists(st.text(min_size=1), max_size=10))
def test_update_values_deduplicates(values):
    """update_values should keep the first occurrence of each value."""
    cv = CoreValues()
    cv.update_values(values)
    assert cv.statements == list(dict.fromkeys(values))


@given(st.text())
def test_find_value_conflicts_no_negation(text):
    """find_value_conflicts returns empty when no negation tokens appear."""
    cv = CoreValues(["safety"])
    lower = text.lower()
    assume("not safety" not in lower and "no safety" not in lower)
    assume("against safety" not in lower and "violate safety" not in lower)
    assert find_value_conflicts(text, cv) == []
