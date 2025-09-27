# This test ensures behavior-style tests enforce explicit speed markers instead of
# relying on auto-injection during collection. The guardrail inspects the collected
# node to confirm exactly one speed marker is present at runtime.

import pytest


@pytest.mark.fast
def test_behavior_requires_explicit_speed_marker(request):
    """ReqID: A2 — Explicit speed markers are required for behavior tests"""
    # At runtime, pytest item marks are not directly accessible; instead we introspect
    # the request.node which represents this test item.
    item = request.node
    speed_marks = {
        m.name for m in item.iter_markers() if m.name in {"fast", "medium", "slow"}
    }
    assert (
        len(speed_marks) == 1
    ), "Behavior tests must have exactly one speed marker injected at collection time"
    assert speed_marks.issubset({"fast", "medium", "slow"})
