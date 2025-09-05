import re

import pytest

from devsynth.testing.run_tests import _failure_tips


@pytest.mark.fast
def test_failure_tips_contains_core_guidance():
    tips = _failure_tips(2, ["python", "-m", "pytest", "-k", "x"])  # type: ignore[arg-type]
    # Ensure return starts and ends with newlines and contains key lines
    assert tips.startswith("\n") and tips.endswith("\n")
    assert "Pytest exited with code 2." in tips
    assert "Troubleshooting tips:" in tips
    # Spot check a few critical suggestions
    assert "--smoke --speed=fast --no-parallel" in tips
    assert "devsynth doctor" in tips
    assert "--segment --segment-size=50" in tips
    assert "--report" in tips
    # Ensure the original command appears joined
    assert "python -m pytest -k x" in tips
