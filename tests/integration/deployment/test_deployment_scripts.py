import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def scripts_dir(tmp_path, monkeypatch):
    """Provide an isolated copy of deployment scripts."""
    root = Path(__file__).resolve().parents[3] / "scripts" / "deployment"
    tmp_path.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    return root


@pytest.mark.fast
def test_bootstrap_env_refuses_root(scripts_dir):
    result = subprocess.run(
        ["bash", str(scripts_dir / "bootstrap_env.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Please run this script as a non-root user." in result.stderr


@pytest.mark.fast
def test_health_check_validates_url(scripts_dir):
    cmd = f"bash {scripts_dir / 'health_check.sh'} https://example.com invalid-url"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Invalid URL" in result.stderr


@pytest.mark.fast
def test_prometheus_exporter_refuses_root(scripts_dir):
    result = subprocess.run(
        ["python", str(scripts_dir / "prometheus_exporter.py")],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode != 0
    assert "Please run this script as a non-root user." in result.stderr


@pytest.mark.fast
@pytest.mark.parametrize("script", ["start_stack.sh", "stop_stack.sh"])
def test_stack_scripts_env_permissions(tmp_path, scripts_dir, script):
    env_file = tmp_path / ".env.development"
    env_file.write_text("DEVSYNTH_ENV=development")
    env_file.chmod(0o644)
    cmd = f"bash {scripts_dir / script} development"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert (
        "Environment file .env.development must have 600 permissions" in result.stderr
    )
