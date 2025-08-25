import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def test_global_test_isolation_sets_env_and_dirs(tmp_path):
    """Ensure the autouse global_test_isolation fixture sets sane defaults.

    We assert:
    - DEVSYNTH_NO_FILE_LOGGING is set to "1"
    - Project-scoped directories are redirected into a tmp path
    - ORIGINAL_CWD is preserved and cwd is switched during test
    """
    # The autouse fixture should have applied by the time this test runs
    assert os.environ.get("DEVSYNTH_NO_FILE_LOGGING") == "1"

    proj_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
    mem_dir = os.environ.get("DEVSYNTH_MEMORY_PATH")
    logs_dir = os.environ.get("DEVSYNTH_LOG_DIR")

    assert proj_dir and Path(proj_dir).exists()
    assert mem_dir and Path(mem_dir).exists()
    # We don't require logs_dir to exist on disk due to ensure_path_exists patch, but it's set
    assert logs_dir

    original_cwd = os.environ.get("ORIGINAL_CWD")
    assert original_cwd, "ORIGINAL_CWD should be captured by the fixture"
    assert (
        os.getcwd() != original_cwd
    ), "cwd should be switched into a temp project during tests"
