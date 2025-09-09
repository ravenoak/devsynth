import pytest


@pytest.mark.fast
def test_speed_dummy() -> None:
    """Sentinel fast test to ensure marker discipline and CI wiring.

    ReqID: DEV-0000
    """
    assert True
