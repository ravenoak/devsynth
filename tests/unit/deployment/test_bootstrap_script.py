import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"

pytestmark = pytest.mark.fast


def test_bootstrap_script_rejects_invalid_environment():
    """bootstrap.sh should reject unknown environments.

    ReqID: DEP-02"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        cmd = f"cd '{workdir}' && {SCRIPTS_DIR / 'bootstrap.sh'} invalid"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Invalid environment" in result.stderr
    finally:
        shutil.rmtree(workdir)


def test_bootstrap_script_requires_docker():
    """bootstrap.sh should require docker to be installed.

    ReqID: DEP-03"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        cmd = f"cd '{workdir}' && {SCRIPTS_DIR / 'bootstrap.sh'} development"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Docker is required" in result.stderr
    finally:
        shutil.rmtree(workdir)
