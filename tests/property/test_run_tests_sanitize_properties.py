"""Property-based tests for _sanitize_node_ids behavior.

Issue: issues/Expand-test-generation-capabilities.md ReqID: FR-09
"""

import pytest

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.testing.run_tests import _sanitize_node_ids


def _with_optional_line_suffix(s: str) -> str:
    # Append ":<digits>" with 50% probability
    return st.one_of(
        st.just(s), st.integers(min_value=1, max_value=10000).map(lambda n: f"{s}:{n}")
    )


@pytest.mark.property
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda t: "::" not in t and "\n" not in t),
            st.one_of(
                st.just(""),
                st.integers(min_value=1, max_value=99999).map(lambda n: f":{n}"),
            ),
        ).map(lambda t: t[0] + t[1]),
        min_size=1,
        max_size=8,
    )
)
@pytest.mark.medium
def test_sanitize_strips_trailing_line_when_no_function(ids):
    """Strip trailing line numbers when no function part is present.

    Issue: issues/Expand-test-generation-capabilities.md ReqID: FR-09
    """
    # Build inputs: ensure no '::' present in base strings
    raw = [f"tests/unit/{s}" if not s.startswith("tests/") else s for s in ids]
    out = _sanitize_node_ids(raw)
    # No output should end with a trailing ":<digits>" when there is no '::'
    import re

    for s in out:
        if "::" not in s:
            assert re.search(r":\d+$", s) is None, s
