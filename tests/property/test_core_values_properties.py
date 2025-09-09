"""Property-based tests for CoreValues utilities.

Issue: issues/Finalize-dialectical-reasoning.md ReqID: FR-87
"""

import pytest

try:
    from hypothesis import assume, given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.core.values import CoreValues, find_value_conflicts


@pytest.mark.property
@given(st.lists(st.text(min_size=1).filter(lambda s: s.strip()), max_size=10))
@pytest.mark.medium
def test_update_values_deduplicates(values):
    """update_values should keep the first occurrence of each value.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: FR-87
    """
    cv = CoreValues()
    cv.update_values(values)
    expected = [v.strip() for v in dict.fromkeys(values) if v.strip()]
    assert cv.statements == expected


@pytest.mark.property
@given(st.text())
@pytest.mark.medium
def test_find_value_conflicts_no_negation(text):
    """find_value_conflicts returns empty when no negation tokens appear.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: FR-87
    """
    cv = CoreValues(["safety"])
    lower = text.lower()
    assume("not safety" not in lower and "no safety" not in lower)
    assume("against safety" not in lower and "violate safety" not in lower)
    assert find_value_conflicts(text, cv) == []
