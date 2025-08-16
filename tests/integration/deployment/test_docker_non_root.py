import shutil
import subprocess

import pytest


@pytest.mark.slow
@pytest.mark.docker
def test_temporary_container_runs_as_non_root(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("Docker not available")

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "FROM alpine:3.19\n"
        "RUN adduser -D appuser\n"
        "USER appuser\n"
        "CMD ['id', '-u']\n"
    )
    image = "devsynth-temp-non-root"
    try:
        subprocess.run(
            ["docker", "build", "-t", image, str(tmp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["docker", "run", "--rm", image],
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() != "0"
    finally:
        subprocess.run(["docker", "rmi", "-f", image], capture_output=True)
