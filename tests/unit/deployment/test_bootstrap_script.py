import os
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


def test_install_dev_installs_task(tmp_path):
    """install_dev.sh should install task when missing.

    ReqID: DEP-04"""
    home = tmp_path
    bin_dir = home / "bin"
    bin_dir.mkdir()

    install_stub = (
        "#!/usr/bin/env bash\n"
        "set -e\n"
        'while getopts "b:" opt; do\n'
        "  case $opt in\n"
        '    b) bindir="$OPTARG" ;;\n'
        "  esac\n"
        "done\n"
        'mkdir -p "$bindir"\n'
        "cat <<'TASKEOF' > \"$bindir/task\"\n"
        "#!/usr/bin/env bash\n"
        "echo 'Task version v0.0.0'\n"
        "TASKEOF\n"
        'chmod +x "$bindir/task"\n'
    )

    curl = bin_dir / "curl"
    curl.write_text(f"#!/usr/bin/env bash\ncat <<'EOF'\n{install_stub}\nEOF\n")
    os.chmod(curl, 0o755)

    for name in ["poetry", "pip", "pre-commit", "devsynth", "wget"]:
        script = bin_dir / name
        if name == "poetry":
            script.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == 'env' && \"$2\" == 'info' && \"$3\" == '--path' ]]; then\n"
                "  echo '/tmp/venv'\n"
                "fi\n"
                "exit 0\n"
            )
        else:
            script.write_text("#!/usr/bin/env bash\nexit 0\n")
        os.chmod(script, 0o755)

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "XDG_CACHE_HOME": str(home / ".cache"),
        }
    )

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install_dev.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    task_bin = home / ".local" / "bin" / "task"
    assert task_bin.exists()

    version = subprocess.run(
        [str(task_bin), "--version"],
        capture_output=True,
        text=True,
    )
    assert version.stdout.strip() == "Task version v0.0.0"
