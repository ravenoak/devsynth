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
