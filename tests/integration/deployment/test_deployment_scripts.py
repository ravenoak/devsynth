import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"


def test_bootstrap_env_refuses_root():
    result = subprocess.run(
        ["bash", str(SCRIPTS_DIR / "bootstrap_env.sh")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
    assert "Please run this script as a non-root user." in result.stderr


def test_health_check_validates_url():
    cmd = f"{SCRIPTS_DIR / 'health_check.sh'} https://example.com invalid-url"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
    assert "Invalid URL" in result.stderr


def test_prometheus_exporter_refuses_root():
    result = subprocess.run(
        ["python", str(SCRIPTS_DIR / "prometheus_exporter.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=5,
    )
    assert result.returncode != 0
    assert "Please run this script as a non-root user." in result.stderr


def test_prometheus_exporter_env_permissions(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("EXPORTER_PORT=9300")
    env_file.chmod(0o644)
    cmd = f"python {SCRIPTS_DIR / 'prometheus_exporter.py'}"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=5,
    )
    assert result.returncode != 0
    assert "Environment file" in result.stderr


def test_publish_image_env_permissions(tmp_path):
    env_file = tmp_path / ".env.production"
    env_file.write_text("DEVSYNTH_IMAGE_TAG=test")
    env_file.chmod(0o644)
    cmd = f"{SCRIPTS_DIR / 'publish_image.sh'}"
    result = subprocess.run(
        ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "Environment file .env.production must have 600 permissions" in result.stderr
