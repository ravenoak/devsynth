from pathlib import Path

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.exceptions import DevSynthError


@pytest.mark.fast
def test_run_generated_tests_fails(tmp_path: Path) -> None:
    """Generated tests execute and fail when unimplemented.

    ReqID: N/A"""
    agent = TestAgent()
    agent.scaffold_integration_tests(["beta"], output_dir=tmp_path)
    with pytest.raises(DevSynthError) as exc:
        agent.run_generated_tests(tmp_path)
    assert "NotImplementedError" in str(exc.value)
