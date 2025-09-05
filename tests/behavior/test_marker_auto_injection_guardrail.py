# This test intentionally defines a behavior-like test without an explicit speed marker.
# We simulate a pytest-bdd scenario wrapper by placing it under tests/behavior/ and relying
# on tests/conftest.py's pytest_collection_modifyitems to auto-inject exactly one speed marker.
#
# The guardrail: ensure exactly one of {fast, medium, slow} is present at runtime.


def test_behavior_auto_inject_speed_marker(request):
    """ReqID: A2 — Auto-injection of exactly one speed marker for behavior tests"""
    # At runtime, pytest item marks are not directly accessible; instead we introspect
    # the request.node which represents this test item.
    item = request.node
    speed_marks = {
        m.name for m in item.iter_markers() if m.name in {"fast", "medium", "slow"}
    }
    # The collection hook is expected to add a default 'fast' mark for behavior tests lacking it.
    assert (
        len(speed_marks) == 1
    ), "Behavior tests must have exactly one speed marker injected at collection time"
    assert speed_marks.issubset({"fast", "medium", "slow"})
