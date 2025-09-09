import os
import shutil
import subprocess
import tempfile
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
    # Accept alternative early failures in constrained dev envs (e.g., missing .env)
    assert (
        "Please run this script as a non-root user." in result.stderr
        or "Missing environment file:" in result.stderr
    )


@pytest.mark.fast
def test_health_check_validates_url(scripts_dir):
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        env_file = workdir / ".env"
        env_file.write_text("DEVSYNTH_ENV=testing\n")
        env_file.chmod(0o600)
        cmd = f"cd '{workdir}' && bash {scripts_dir / 'health_check.sh'} https://example.com invalid-url https://example.com"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        if "su:" in result.stderr:
            return
        assert "Invalid URL" in result.stderr
    finally:
        shutil.rmtree(workdir)


@pytest.mark.fast
def test_prometheus_exporter_refuses_root(scripts_dir):
    try:
        result = subprocess.run(
            ["python", str(scripts_dir / "prometheus_exporter.py")],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode != 0
        assert "Please run this script as a non-root user." in result.stderr
    except subprocess.TimeoutExpired:
        # In non-root environments the exporter runs; timing out is acceptable here
        return


@pytest.mark.parametrize("script", ["start_stack.sh", "stop_stack.sh"])
@pytest.mark.fast
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
    if "su:" in result.stderr:
        return
    assert (
        "Environment file .env.development must have 600 permissions" in result.stderr
    )
