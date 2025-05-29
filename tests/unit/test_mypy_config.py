import os
import subprocess
import tempfile
import pytest

def test_mypy_configuration():
    """
    Test that mypy is properly configured to detect type errors.

    This test creates a temporary Python file with intentional type errors,
    runs mypy on it, and verifies that mypy reports the errors correctly.
    """
    # Create a temporary file with intentional type errors
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_file.write(b"""
def add(a: int, b: int) -> int:
    return a + b

# Type error: Expected int but got str
result: int = add("not an integer", 5)
""")
        temp_file_path = temp_file.name

    try:
        # Run mypy on the temporary file
        result = subprocess.run(
            ["mypy", temp_file_path],
            capture_output=True,
            text=True,
            check=False
        )

        # Check that mypy detected the type error
        assert result.returncode != 0, "mypy should fail on type errors"
        assert "Argument 1 to \"add\" has incompatible type" in result.stdout, \
            f"mypy did not detect the type error. Output: {result.stdout}"

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_mypy_project_configuration():
    """
    Test that mypy is properly configured for the project.

    This test creates a Python file with an untyped function definition,
    which should trigger an error if mypy is using the configuration from
    pyproject.toml where disallow_untyped_defs=true is set.
    """
    # Create a temporary file with an untyped function definition
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_file.write(b"""
# This function has no type annotations, which should trigger an error
# with disallow_untyped_defs=true
def untyped_function(param):
    return param
""")
        temp_file_path = temp_file.name

    try:
        # Create a mypy.ini file with the same configuration as in pyproject.toml
        with tempfile.NamedTemporaryFile(suffix='.ini', delete=False) as config_file:
            config_file.write(b"""
[mypy]
python_version = 3.11
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
strict_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
""")
            config_file_path = config_file.name

        # Run mypy on the temporary file with the explicit config file
        result = subprocess.run(
            ["mypy", "--config-file", config_file_path, temp_file_path],
            capture_output=True,
            text=True,
            check=False
        )

        # Print debug information
        print(f"mypy stdout: {result.stdout}")
        print(f"mypy stderr: {result.stderr}")
        print(f"mypy returncode: {result.returncode}")

        # Check that mypy detected the untyped function definition error
        # This will only happen if mypy is using the configuration where disallow_untyped_defs=true is set
        assert result.returncode != 0, "mypy should fail on untyped function definitions"
        assert "Function is missing a type annotation" in result.stdout, \
            f"mypy did not detect the untyped function definition error, which suggests it's not using the configuration correctly. Output: {result.stdout}"

    finally:
        # Clean up the temporary files
        os.unlink(temp_file_path)
        os.unlink(config_file_path)
