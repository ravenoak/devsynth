import pytest

@pytest.mark.fast
def test_speed_marker_dummy():
    """Sentinel test to ensure marker discipline tooling and CI wiring have at least one test in each speed bucket.
    This test is intentionally trivial and should remain present. See docs/tasks.md and .junie/guidelines.md.
    """
    assert True
