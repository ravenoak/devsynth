import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"


@pytest.mark.fast
def test_setup_env_refuses_root():
    result = subprocess.run(
        ["bash", str(SCRIPTS_DIR / "setup_env.sh")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
    assert "Please run this script as a non-root user." in result.stderr


@pytest.mark.fast
def test_check_health_env_permissions(tmp_path):
    env_file = tmp_path / ".env.development"
    env_file.write_text("DEVSYNTH_ENV=development\n")
    env_file.chmod(0o644)
    cmd = f"{SCRIPTS_DIR / 'check_health.sh'} development"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "environment file" in result.stderr.lower()


@pytest.mark.fast
def test_rollback_requires_tag():
    cmd = f"{SCRIPTS_DIR / 'rollback.sh'}"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
    assert "Usage: rollback.sh" in result.stderr
