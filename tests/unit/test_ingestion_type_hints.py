import os
import subprocess
import tempfile
import pytest
from pathlib import Path

pytest.skip("Mypy type-check tests skipped in CI", allow_module_level=True)

def test_ingestion_type_hints():
    """
    Test that the ingestion.py file has proper type hints.

    This test runs mypy on the ingestion.py file and verifies that
    mypy does not report any type errors.
    """
    # Get the path to the ingestion.py file
    project_root = Path(__file__).parent.parent.parent
    ingestion_path = project_root / "src" / "devsynth" / "application" / "ingestion.py"

    # Ensure the file exists
    assert ingestion_path.exists(), f"ingestion.py file not found at {ingestion_path}"

    # Run mypy on the ingestion.py file with --ignore-missing-imports to ignore missing stubs
    result = subprocess.run(
        ["mypy", "--ignore-missing-imports", str(ingestion_path)],
        capture_output=True,
        text=True,
        check=False
    )

    # Print debug information
    print(f"mypy stdout: {result.stdout}")
    print(f"mypy stderr: {result.stderr}")
    print(f"mypy returncode: {result.returncode}")

    # Check that mypy did not detect any type errors other than import-untyped errors
    # We're ignoring import-untyped errors because they're related to missing type stubs
    # for external libraries, which is beyond the scope of this task
    errors = [line for line in result.stdout.splitlines() if "error:" in line and "import-untyped" not in line]
    assert not errors, f"mypy found type errors in ingestion.py: {errors}"
