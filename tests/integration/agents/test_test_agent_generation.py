from pathlib import Path

import pytest

from devsynth.application.agents import test as test_agent_module
from devsynth.application.agents.test import TestAgent


@pytest.mark.fast
def test_scaffold_hook_creates_placeholder(tmp_path: Path) -> None:
    """Module-level hook writes placeholder integration tests.

    ReqID: N/A"""
    written = test_agent_module.write_scaffolded_tests(tmp_path, ["sample"])
    file_path = tmp_path / "test_sample.py"
    assert file_path in written
    content = file_path.read_text()
    assert "pytestmark = pytest.mark.skip" in content
    assert content == written[file_path]


@pytest.mark.fast
def test_process_generates_tests_and_scaffolds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TestAgent.process generates tests and scaffolds integration files.

    ReqID: N/A"""
    agent = TestAgent()
    monkeypatch.setattr(agent, "generate_text", lambda prompt: "generated tests")

    wsde_sentinel = object()
    monkeypatch.setattr(
        agent,
        "create_wsde",
        lambda content, content_type, metadata: wsde_sentinel,
    )

    result = agent.process(
        {
            "context": "ctx",
            "specifications": "spec",
            "integration_test_names": ["alpha"],
            "integration_output_dir": tmp_path,
        }
    )

    assert result["tests"] == "generated tests"
    assert result["wsde"] is wsde_sentinel
    assert "test_alpha.py" in result["integration_tests"]
    scaffold = tmp_path / "test_alpha.py"
    assert scaffold.exists()
    assert "pytestmark = pytest.mark.skip" in scaffold.read_text()
