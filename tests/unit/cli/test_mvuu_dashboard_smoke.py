import subprocess
import sys
from unittest import mock

import pytest


@pytest.mark.smoke
def test_mvuu_dashboard_module_no_run_avoids_subprocess():
    # Ensure running the module with --no-run exits cleanly and does not spawn subprocesses
    with mock.patch.object(subprocess, "run") as mocked_run:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "devsynth.application.cli.commands.mvuu_dashboard_cmd",
                "--no-run",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
        )
    # The outer subprocess.run executed our Python process; it should have succeeded
    assert proc.returncode == 0
    # And our inner mocked subprocess.run should not have been called because --no-run short-circuits
    mocked_run.assert_not_called()
