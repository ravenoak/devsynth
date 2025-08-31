import pytest


@pytest.mark.fast
def test_speed_dummy() -> None:
    """Sentinel fast test for CI tooling and marker discipline."""
    assert True
