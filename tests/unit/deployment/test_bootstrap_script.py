import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"


@pytest.mark.fast
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


@pytest.mark.fast
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


@pytest.mark.fast
def test_install_dev_installs_task(tmp_path):
    """install_dev.sh should install go-task when absent.

    ReqID: DEP-05"""

    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    task_stub = tmp_path / "task"
    task_stub.write_text(
        "#!/usr/bin/env bash\nif [[ $1 == '--version' ]]; then echo 'Task version 0.0.0'; fi\n"
    )
    task_stub.chmod(0o755)
    tar_path = tmp_path / "task.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(task_stub, arcname="task")

    curl_script = bin_dir / "curl"
    curl_script.write_text(f"#!/usr/bin/env bash\ncat '{tar_path}'\n")
    curl_script.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home)
    python_dir = Path(shutil.which("python")).parent
    env["PATH"] = (
        f"{bin_dir}:{python_dir}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    )

    install_script = ROOT / "scripts" / "install_dev.sh"
    cmd = (
        "awk '/^# Ensure Poetry manages a dedicated virtual environment/ {exit} {print}' "
        f"'{install_script}' | bash"
    )
    subprocess.run(["bash", "-c", cmd], check=True, env=env)

    task_bin = home / ".local" / "bin" / "task"
    assert task_bin.exists()
    result = subprocess.run(
        [str(task_bin), "--version"], capture_output=True, text=True
    )
    assert result.stdout.strip() == "Task version 0.0.0"
