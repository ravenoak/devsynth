"""Utilities for resolving behavior feature file paths."""

from __future__ import annotations

from pathlib import Path


def feature_path(source: str, *parts: str) -> str:
    """Return an absolute path to a feature file."""

    # Get the project root by finding the tests directory and going up one level
    test_file = Path(source).resolve()

    # Find the tests directory in the path
    current = test_file
    while current.name != "tests" and current.parent != current:
        current = current.parent

    if current.name == "tests":
        project_root = current.parent
    else:
        # Fallback: assume we're in a test file and go up until we find the project root
        # This handles cases where the file structure is different
        project_root = test_file.parents[3] if len(test_file.parents) > 3 else test_file.parents[-1]

    # Build the full path to the feature file
    result = str(project_root / "tests" / "behavior" / "features" / Path(*parts))
    return result
