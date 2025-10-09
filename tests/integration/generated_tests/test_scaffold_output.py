"""Verify that integration test scaffolds are written to disk."""

from pathlib import Path

import pytest

from devsynth.application.agents.test import TestAgent

pytestmark = [pytest.mark.medium]


def test_scaffold_integration_tests_creates_files(tmp_path: Path) -> None:
    agent = TestAgent()
    result = agent.scaffold_integration_tests(["sample"], output_dir=tmp_path)

    expected = tmp_path / "test_sample.py"
    assert expected.exists(), "scaffold file should be created"
    content = expected.read_text()
    assert "pytest.mark.skip" in content
    assert "Integration test scaffold for sample" in content
    assert "test_sample.py" in result
