import subprocess
import sys
from pathlib import Path


def test_speed_option_recognized():
    repo_root = Path(__file__).resolve().parents[3]
    test_file = repo_root / "tests" / "tmp_speed_dummy.py"
    test_file.write_text(
        "import pytest\n@pytest.mark.fast\ndef test_dummy():\n    assert True\n"
    )
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--speed=fast",
                "-m",
                "fast",
                str(test_file),
            ],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
    finally:
        if test_file.exists():
            test_file.unlink()
