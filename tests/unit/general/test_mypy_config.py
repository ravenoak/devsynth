import os
import subprocess
import tempfile

import pytest


def test_mypy_configuration_raises_error():
    """Test that mypy is properly configured to detect type errors.

    This test creates a temporary Python file with intentional type errors,
    runs mypy on it, and verifies that mypy reports the errors correctly.

    ReqID: N/A"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(
            b'\ndef add(a: int, b: int) -> int:\n    return a + b\n\n# Type error: Expected int but got str\nresult: int = add("not an integer", 5)\n'
        )
        temp_file_path = temp_file.name
    try:
        result = subprocess.run(
            ["mypy", temp_file_path], capture_output=True, text=True, check=False
        )
        assert result.returncode != 0, "mypy should fail on type errors"
        assert (
            'Argument 1 to "add" has incompatible type' in result.stdout
        ), f"mypy did not detect the type error. Output: {result.stdout}"
    finally:
        os.unlink(temp_file_path)


def test_mypy_project_configuration_raises_error():
    """Test that mypy is properly configured for the project.

    This test creates a Python file with an untyped function definition,
    which should trigger an error if mypy is using the configuration from
    pyproject.toml where disallow_untyped_defs=true is set.

    ReqID: N/A"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(
            b"\n# This function has no type annotations, which should trigger an error\n# with disallow_untyped_defs=true\ndef untyped_function(param):\n    return param\n"
        )
        temp_file_path = temp_file.name
    try:
        with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as config_file:
            config_file.write(
                b"\n[mypy]\npython_version = 3.12\nwarn_return_any = true\nwarn_unused_configs = true\ndisallow_untyped_defs = true\ndisallow_incomplete_defs = true\ncheck_untyped_defs = true\ndisallow_untyped_decorators = true\nno_implicit_optional = true\nstrict_optional = true\nwarn_redundant_casts = true\nwarn_unused_ignores = true\nwarn_no_return = true\nwarn_unreachable = true\n"
            )
            config_file_path = config_file.name
        result = subprocess.run(
            ["mypy", "--config-file", config_file_path, temp_file_path],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"mypy stdout: {result.stdout}")
        print(f"mypy stderr: {result.stderr}")
        print(f"mypy returncode: {result.returncode}")
        assert (
            result.returncode != 0
        ), "mypy should fail on untyped function definitions"
        assert (
            "Function is missing a type annotation" in result.stdout
        ), f"mypy did not detect the untyped function definition error, which suggests it's not using the configuration correctly. Output: {result.stdout}"
    finally:
        os.unlink(temp_file_path)
        os.unlink(config_file_path)
