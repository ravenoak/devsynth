from pathlib import Path

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.exceptions import DevSynthError


@pytest.mark.fast
def test_run_generated_tests_pass(tmp_path: Path) -> None:
    """Generated placeholder tests execute successfully.

    ReqID: N/A"""
    agent = TestAgent()
    agent.scaffold_integration_tests(["beta"], output_dir=tmp_path)
    output = agent.run_generated_tests(tmp_path)
    assert "1 passed" in output


@pytest.mark.fast
def test_run_generated_tests_failure(tmp_path: Path) -> None:
    """Failing assertions surface through DevSynthError.

    ReqID: N/A"""
    agent = TestAgent()
    failing = tmp_path / "test_fail.py"
    failing.write_text("def test_fail() -> None:\n    assert False\n")
    with pytest.raises(DevSynthError) as exc:
        agent.run_generated_tests(tmp_path)
    assert "assert False" in str(exc.value)
