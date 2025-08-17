import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.slow
@pytest.mark.docker
def test_deploy_script_requires_docker(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("Docker not available")

    repo_root = Path(__file__).resolve().parents[3]
    env_file = tmp_path / ".env.development"
    env_file.write_text("DEVSYNTH_ENV=development\n")
    env_file.chmod(0o600)

    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            "1000:1000",
            "-v",
            f"{repo_root}:/repo",
            "-v",
            f"{env_file}:/repo/.env.development",
            "python:3.11",
            "bash",
            "-lc",
            "cd /repo && scripts/deployment/deploy.sh development",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Docker is required but could not be found in PATH." in result.stderr
