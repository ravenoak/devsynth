import pytest

from devsynth import DevSynthLogger


@pytest.mark.fast
def test_speed_dummy():
    """Sentinel test for speed marker validation.

    ReqID: DEV-0000
    """
    # Ensure DevSynth exports logging helpers via __getattr__
    logger = DevSynthLogger(__name__)
    assert logger is not None
