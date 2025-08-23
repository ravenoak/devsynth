import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.fast
def test_run_tests_command_succeeds_without_optional_providers() -> None:
    """``devsynth run-tests`` should exit 0 without external providers.

    ReqID: FR-22
    """

    if os.environ.get("DEVSYNTH_INNER_TEST") == "1":
        pytest.skip("inner run")

    env = os.environ.copy()
    env["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"
    env["DEVSYNTH_INNER_TEST"] = "1"
    env["PYTEST_ADDOPTS"] = "-k test_dummy"
    result = subprocess.run(
        [
            "devsynth",
            "run-tests",
            "--speed",
            "fast",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=Path(__file__).resolve().parents[5],
    )
    assert result.returncode == 0, result.stdout + result.stderr
