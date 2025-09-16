# flake8: noqa: E501
import os

import pytest

from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.enforce_coverage_threshold",
        lambda *a, **k: 100.0,
    )


class DummyBridge(UXBridge):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def ask_question(self, message: str, *, choices=None, default=None, show_default=True) -> str:  # type: ignore[override]
        return default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:  # type: ignore[override]
        return default

    def display_result(self, message: str, *, highlight: bool = False, message_type: str | None = None) -> None:  # type: ignore[override]
        self.messages.append(message)


@pytest.mark.fast
def test_report_flag_with_missing_directory_prints_warning(
    tmp_path, monkeypatch
) -> None:
    """ReqID: CLI-RT-12 — Report flag prints helpful message even if dir missing.

    Simulate a successful run with --report but test_reports/ absent. The CLI
    should not crash; it should print a yellow advisory.
    """

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        # Simulate success with some output
        return True, "OK"

    monkeypatch.setenv("PWD", str(tmp_path))
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    # Ensure test_reports does not exist
    report_dir = tmp_path / "test_reports"
    if report_dir.exists():
        if report_dir.is_dir():
            for p in report_dir.iterdir():
                if p.is_file():
                    p.unlink()
            report_dir.rmdir()
        else:
            report_dir.unlink()

    bridge = DummyBridge()

    # Invoke with report=True
    run_tests_cmd(target="unit-tests", speeds=["fast"], report=True, bridge=bridge)

    # Should include success message and a yellow advisory about missing dir
    joined = "\n".join(bridge.messages)
    assert "Tests completed successfully" in joined
    assert "Report flag was set but test_reports/ was not found" in joined


@pytest.mark.fast
def test_smoke_mode_sets_env_and_disables_parallel(monkeypatch) -> None:
    """ReqID: CLI-RT-01 — Smoke mode disables plugin autoload and xdist.

    Validate that smoke=True sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and flips
    no_parallel internally (i.e., run_tests receives parallel=False).
    """

    captured = {}

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        captured["args"] = args
        captured["kwargs"] = kwargs
        return True, "OK"

    # Ensure the var is not pre-set so smoke path can set it
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(target="unit-tests", speeds=[], smoke=True, bridge=bridge)

    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    # run_tests args: (..., parallel, ...)
    assert captured["args"][4] is False  # type: ignore[index]


@pytest.mark.fast
def test_no_parallel_maps_to_n0(monkeypatch) -> None:
    """ReqID: CLI-RT-02 — --no-parallel results in parallel=False.

    Ensure the CLI passes parallel=False to the runner when --no-parallel is set.
    """

    captured = {}

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        captured["args"] = args
        return True, "OK"

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(target="unit-tests", speeds=["fast"], no_parallel=True, bridge=bridge)

    assert captured["args"][4] is False  # type: ignore[index]


@pytest.mark.fast
def test_emit_coverage_messages_reports_artifacts(tmp_path, monkeypatch) -> None:
    """Coverage helper announces artifact locations when present."""

    from devsynth.application.cli.commands import run_tests_cmd as module

    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<html>ok</html>")

    json_path = tmp_path / "test_reports" / "coverage.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text("{\n  \"totals\": {\"percent_covered\": 100.0}\n}")

    monkeypatch.setattr(module, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(module, "COVERAGE_JSON_PATH", json_path)

    bridge = DummyBridge()
    module._emit_coverage_artifact_messages(bridge)

    joined = "\n".join(bridge.messages)
    assert "HTML coverage report available" in joined
    assert "Coverage JSON written to" in joined
