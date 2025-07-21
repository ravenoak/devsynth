import os
import subprocess
import tempfile
import pytest
from pathlib import Path
pytest.skip('Mypy type-check tests skipped in CI', allow_module_level=True)


def test_ingestion_type_hints_raises_error():
    """Test that the ingestion.py file has proper type hints.

This test runs mypy on the ingestion.py file and verifies that
mypy does not report any type errors.

ReqID: N/A"""
    project_root = Path(__file__).parent.parent.parent
    ingestion_path = (project_root / 'src' / 'devsynth' / 'application' /
        'ingestion.py')
    assert ingestion_path.exists(
        ), f'ingestion.py file not found at {ingestion_path}'
    result = subprocess.run(['mypy', '--ignore-missing-imports', str(
        ingestion_path)], capture_output=True, text=True, check=False)
    print(f'mypy stdout: {result.stdout}')
    print(f'mypy stderr: {result.stderr}')
    print(f'mypy returncode: {result.returncode}')
    errors = [line for line in result.stdout.splitlines() if 'error:' in
        line and 'import-untyped' not in line]
    assert not errors, f'mypy found type errors in ingestion.py: {errors}'
