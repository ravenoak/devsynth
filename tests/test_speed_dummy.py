import pytest


@pytest.mark.fast
def test_speed_dummy_sentinel():
    """Sentinel test to ensure marker discipline control path is always valid.
    ReqID: QA-SPEED-SENTINEL
    """
    assert True
