"""Template integration tests for generated modules.

Copy this file when scaffolding integration tests for new modules and replace
placeholders with concrete assertions.
This example demonstrates a simple workflow involving file output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.skip(reason="Template for generated module integration tests"),
    pytest.mark.medium,
]


def process_data(value: int, output_path: Path) -> Path:
    """Write a doubled value to ``output_path`` as JSON and return the path."""
    result = {"doubled": value * 2}
    output_path.write_text(json.dumps(result))
    return output_path


def test_generated_module_workflow(tmp_path: Path) -> None:
    """Verify the generated module can create and read output files."""
    output_file = tmp_path / "result.json"
    returned_path = process_data(21, output_file)

    assert returned_path == output_file
    assert output_file.exists(), "process_data should create the file"

    loaded = json.loads(output_file.read_text())
    assert loaded["doubled"] == 42
