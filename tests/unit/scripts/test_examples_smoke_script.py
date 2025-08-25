"""Smoke tests for scripts/examples_smoke.py. ReqID: QA-07

These tests ensure the examples smoke script can run in a constrained
(test/no-network) environment by mocking its external interactions.
"""

from types import SimpleNamespace

import pytest

import scripts.examples_smoke as examples_smoke


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    """Prevent actual subprocess calls by replacing examples_smoke.run.

    We simulate successful command execution and capture invocations implicitly.
    """

    def fake_run(cmd, cwd=None):
        # Simulate a successful subprocess execution
        return 0, "OK", ""

    monkeypatch.setattr(examples_smoke, "run", fake_run)


def test_main_default_examples_succeeds(monkeypatch):
    """Default invocation should succeed when analysis is mocked. ReqID: QA-07"""

    # Avoid depending on repo structure; ensure select_examples returns some paths
    monkeypatch.setattr(
        examples_smoke,
        "select_examples",
        lambda names: [examples_smoke.REPO_ROOT / "examples" / name for name in names],
    )

    # Pretend all example paths exist regardless of filesystem
    class _FakePath:
        def __init__(self, p):
            self._p = p

        def exists(self):
            return True

        def relative_to(self, root):
            return self._p

    monkeypatch.setattr(
        examples_smoke,
        "select_examples",
        lambda names: [_FakePath(examples_smoke.EXAMPLES_DIR / n) for n in names],
    )

    # check_cli_help and analyze_example are fast-pass no-ops under test
    monkeypatch.setattr(examples_smoke, "check_cli_help", lambda: None)
    monkeypatch.setattr(examples_smoke, "analyze_example", lambda p: None)

    assert examples_smoke.main([]) == 0


def test_main_reports_failure_when_analyze_raises(monkeypatch):
    """When an example analysis fails, the script should return non-zero. ReqID: QA-07"""

    class _FakePath:
        def __init__(self, p):
            self._p = p

        def exists(self):
            return True

        def relative_to(self, root):
            return self._p

    monkeypatch.setattr(
        examples_smoke,
        "select_examples",
        lambda names: [_FakePath(examples_smoke.EXAMPLES_DIR / n) for n in names],
    )

    monkeypatch.setattr(examples_smoke, "check_cli_help", lambda: None)

    def explode(_):
        raise SystemExit(2)

    monkeypatch.setattr(examples_smoke, "analyze_example", explode)

    assert examples_smoke.main(["--examples", "calculator"]) == 1
