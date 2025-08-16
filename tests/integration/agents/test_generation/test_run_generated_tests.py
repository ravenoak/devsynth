from pathlib import Path

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.exceptions import DevSynthError
from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_run_tests_fails_when_tests_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TestAgent.run_tests raises DevSynthError on failing tests.

    ReqID: N/A"""
    (tmp_path / "test_fail.py").write_text(
        "import pytest\npytestmark = pytest.mark.fast\n\n"
        "def test_fail() -> None:\n    assert False\n"
    )
    monkeypatch.setitem(
        run_tests_module.TARGET_PATHS, "integration-tests", str(tmp_path)
    )
    monkeypatch.setattr(
        run_tests_module, "COLLECTION_CACHE_DIR", str(tmp_path / "cache")
    )
    agent = TestAgent()
    with pytest.raises(DevSynthError):
        agent.run_tests("integration-tests", speed="fast")


@pytest.mark.fast
def test_run_tests_succeeds_when_tests_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TestAgent.run_tests returns output when tests pass.

    ReqID: N/A"""
    (tmp_path / "test_pass.py").write_text(
        "import pytest\npytestmark = pytest.mark.fast\n\n"
        "def test_pass() -> None:\n    assert True\n"
    )
    monkeypatch.setitem(
        run_tests_module.TARGET_PATHS, "integration-tests", str(tmp_path)
    )
    monkeypatch.setattr(
        run_tests_module, "COLLECTION_CACHE_DIR", str(tmp_path / "cache")
    )
    agent = TestAgent()
    output = agent.run_tests("integration-tests", speed="fast")
    assert "1 passed" in output
