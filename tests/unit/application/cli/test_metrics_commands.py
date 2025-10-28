from __future__ import annotations

import importlib
import importlib.util
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

align_mod = importlib.import_module(
    "devsynth.application.cli.commands.alignment_metrics_cmd"
)
test_mod = importlib.import_module("devsynth.application.cli.commands.test_metrics_cmd")


def _dummy_progress(*args, **kwargs):

    @contextmanager
    def _cm():

        class Dummy:

            def update(self, **_):
                pass

        yield Dummy()

    return _cm()


@pytest.mark.medium
def test_alignment_metrics_cmd_success(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.json"
    report_path = tmp_path / "report.md"
    monkeypatch.setattr(
        align_mod,
        "bridge",
        types.SimpleNamespace(
            print=lambda *a, **k: None, create_progress=_dummy_progress
        ),
    )
    monkeypatch.setattr(align_mod, "get_all_files", lambda p: ["a.txt"])
    monkeypatch.setattr(align_mod, "calculate_alignment_coverage", lambda f: {"cov": 1})
    monkeypatch.setattr(
        align_mod,
        "calculate_alignment_issues",
        lambda f: {
            "total_issues": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
        },
    )
    monkeypatch.setattr(align_mod, "load_historical_metrics", lambda f: [])
    saved = {}
    monkeypatch.setattr(align_mod, "save_metrics", lambda m, f, h: saved.update(m))
    monkeypatch.setattr(align_mod, "display_metrics", lambda m, h, **_: None)
    monkeypatch.setattr(
        align_mod,
        "generate_metrics_report",
        lambda m, h, o, **_: Path(o).write_text("ok"),
    )
    assert align_mod.alignment_metrics_cmd(
        path=str(tmp_path), metrics_file=str(metrics_path), output=str(report_path)
    )
    assert saved["cov"] == 1
    assert report_path.read_text() == "ok"


@pytest.mark.medium
def test_alignment_metrics_cmd_failure(monkeypatch):
    outputs = []
    monkeypatch.setattr(
        align_mod,
        "bridge",
        types.SimpleNamespace(
            print=lambda m: outputs.append(m), create_progress=_dummy_progress
        ),
    )
    monkeypatch.setattr(
        align_mod,
        "get_all_files",
        lambda p: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert align_mod.alignment_metrics_cmd(path=".") is False
    assert any("Error collecting alignment metrics" in o for o in outputs)


def _dummy_console():
    return types.SimpleNamespace(status=lambda *a, **k: _dummy_progress())


@pytest.mark.medium
def test_test_metrics_cmd_writes_report(monkeypatch, tmp_path):
    out_file = tmp_path / "rep.md"
    prints = []
    monkeypatch.setattr(
        test_mod, "bridge", types.SimpleNamespace(print=lambda m: prints.append(m))
    )
    monkeypatch.setattr(test_mod, "Console", _dummy_console)
    monkeypatch.setattr(test_mod, "get_commit_history", lambda d: [{}])
    monkeypatch.setattr(
        test_mod,
        "calculate_metrics",
        lambda c: {
            "total_commits": 1,
            "test_first_commits": 1,
            "code_first_commits": 0,
            "mixed_commits": 0,
            "test_first_ratio": 1.0,
            "code_first_ratio": 0.0,
            "mixed_ratio": 0.0,
            "test_files_count": 0,
            "code_files_count": 0,
            "test_to_code_ratio": 0.0,
            "recent_test_first_commits": [],
            "recent_code_first_commits": [],
        },
    )
    monkeypatch.setattr(test_mod, "generate_metrics_report", lambda m: "report")
    test_mod.test_metrics_cmd(days=1, output_file=str(out_file))
    assert out_file.read_text() == "report"
    assert any("Metrics report written to" in str(p) for p in prints)


@pytest.mark.medium
def test_test_metrics_cmd_no_commits(monkeypatch):
    prints = []
    monkeypatch.setattr(
        test_mod, "bridge", types.SimpleNamespace(print=lambda m: prints.append(m))
    )
    monkeypatch.setattr(test_mod, "Console", _dummy_console)
    monkeypatch.setattr(test_mod, "get_commit_history", lambda d: [])
    test_mod.test_metrics_cmd(days=1)
    assert any("No commits" in str(p) for p in prints)
