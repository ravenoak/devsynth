import types
from types import SimpleNamespace

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_run_tests_uses_keyword_filter_for_lmstudio(monkeypatch):
    """When extra_marker contains requires_resource('lmstudio'),
    run_tests should collect with -k lmstudio and execute node IDs directly.
    """

    # Fake subprocess.run for collection step
    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        # Ensure '-k' keyword is applied
        assert "-k" in cmd and "lmstudio" in cmd
        # Simulate pytest --collect-only -q output with a single node id
        stdout = "tests/unit/integration_lmstudio_test.py::test_api_roundtrip\n"
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    # Fake Popen for execution step
    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # The command should include the collected node id rather than '-m'
            assert any(
                s.startswith(
                    "tests/unit/integration_lmstudio_test.py::test_api_roundtrip"
                )
                for s in cmd
            ), f"expected node id in cmd, got: {cmd}"
            self.returncode = 0

        def communicate(self):
            return ("ok\n", "")

    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert "ok" in output or output == ""
