import pytest


@pytest.mark.fast
def test_speed_dummy() -> None:
    """Sentinel fast test to ensure test discovery works and enforces marker discipline.

    ReqID: DEV-0000
    """
    assert True
