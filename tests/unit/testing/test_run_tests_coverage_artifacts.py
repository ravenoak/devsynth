from __future__ import annotations

import builtins
import json
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture
def coverage_test_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> SimpleNamespace:
    """Configure run_tests coverage paths inside a temporary directory."""

    monkeypatch.chdir(tmp_path)
    coverage_json_path = tmp_path / "reports" / "coverage.json"
    html_dir = tmp_path / "reports" / "html"
    legacy_dir = tmp_path / "legacy" / "html"
    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", coverage_json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(rt, "LEGACY_HTML_DIRS", (legacy_dir,))
    return SimpleNamespace(
        coverage_json=coverage_json_path,
        html_dir=html_dir,
        legacy_dir=legacy_dir,
    )


@pytest.mark.fast
def test_reset_coverage_artifacts_removes_files_and_directories(
    coverage_test_environment: SimpleNamespace,
) -> None:
    """ReqID: COV-ART-01 — Reset removes data files and HTML directories."""

    env = coverage_test_environment
    data_file = Path(".coverage")
    data_file.write_text("data")
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text("legacy")
    Path("coverage.json").write_text("legacy-json")
    env.html_dir.mkdir(parents=True, exist_ok=True)
    (env.html_dir / "index.html").write_text("old-html")
    env.legacy_dir.mkdir(parents=True, exist_ok=True)
    (env.legacy_dir / "index.html").write_text("old-legacy")

    rt._reset_coverage_artifacts()

    assert not data_file.exists()
    assert not env.coverage_json.exists()
    assert not Path("coverage.json").exists()
    assert not env.html_dir.exists()
    assert not env.legacy_dir.exists()
    # Parents should remain available for subsequent reports
    assert env.coverage_json.parent.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_warns_when_data_missing(
    coverage_test_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: COV-ART-02 — Warn and skip when the .coverage data file is absent."""

    module = ModuleType("coverage")

    class UnexpectedCoverage:  # pragma: no cover - defensive
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError(
                "Coverage should not be instantiated without data file"
            )

    module.Coverage = UnexpectedCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.WARNING)

    rt._ensure_coverage_artifacts()

    assert "data file missing" in caplog.text
    assert not coverage_test_environment.coverage_json.exists()
    assert not coverage_test_environment.html_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_warns_when_no_measured_files(
    coverage_test_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: COV-ART-03 — Warn when coverage data has no measured files."""

    module = ModuleType("coverage")
    data_file = Path(".coverage")
    data_file.write_text("stub")

    class NoMeasuredCoverage:
        def __init__(self, data_file: str) -> None:  # noqa: D401 - simple stub
            self.data_file = data_file

        def load(self) -> None:
            return None

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: [])

        def html_report(
            self, *_args: object, **_kwargs: object
        ) -> None:  # pragma: no cover
            raise AssertionError("html_report should not run when no measured files")

        def json_report(
            self, *_args: object, **_kwargs: object
        ) -> None:  # pragma: no cover
            raise AssertionError("json_report should not run when no measured files")

    module.Coverage = NoMeasuredCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.WARNING)

    rt._ensure_coverage_artifacts()

    assert "no measured files" in caplog.text
    assert not coverage_test_environment.coverage_json.exists()
    assert not coverage_test_environment.html_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_generates_reports_and_syncs_legacy(
    coverage_test_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: COV-ART-04 — Successful generation syncs HTML/JSON artifacts."""

    module = ModuleType("coverage")
    data_file = Path(".coverage")
    data_file.write_text("valid")
    coverage_payload = {"totals": {"percent_covered": 99.9}}

    class SuccessfulCoverage:
        def __init__(self, data_file: str) -> None:
            self.data_file = data_file
            self.loaded = False

        def load(self) -> None:
            self.loaded = True

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: ["src/devsynth/module.py"])

        def html_report(self, directory: str) -> None:
            output = Path(directory)
            output.mkdir(parents=True, exist_ok=True)
            (output / "index.html").write_text("<html>ok</html>")

        def json_report(self, outfile: str) -> None:
            Path(outfile).write_text(json.dumps(coverage_payload))

    module.Coverage = SuccessfulCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    # Pre-create legacy directory with stale contents to exercise synchronization
    coverage_test_environment.legacy_dir.mkdir(parents=True, exist_ok=True)
    (coverage_test_environment.legacy_dir / "stale.html").write_text("old")

    rt._ensure_coverage_artifacts()

    html_index = coverage_test_environment.html_dir / "index.html"
    assert html_index.exists()
    assert "ok" in html_index.read_text()

    legacy_index = coverage_test_environment.legacy_dir / "index.html"
    assert legacy_index.exists()
    assert legacy_index.read_text() == html_index.read_text()

    assert coverage_test_environment.coverage_json.exists()
    assert (
        json.loads(coverage_test_environment.coverage_json.read_text())
        == coverage_payload
    )

    legacy_json = Path("coverage.json")
    assert legacy_json.exists()
    assert json.loads(legacy_json.read_text()) == coverage_payload


@pytest.mark.fast
def test_ensure_coverage_artifacts_skips_when_module_unavailable(
    coverage_test_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: COV-ART-02A — Missing coverage module logs debug message and exits."""

    monkeypatch.delitem(sys.modules, "coverage", raising=False)

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # noqa: ANN001
        if name == "coverage":
            raise ImportError("coverage module unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with caplog.at_level(logging.DEBUG, logger="devsynth.testing.run_tests"):
        rt._ensure_coverage_artifacts()

    assert any("coverage library unavailable" in message for message in caplog.messages)
    assert not coverage_test_environment.coverage_json.exists()
    assert not coverage_test_environment.html_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_html_failure_still_writes_json(
    coverage_test_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: COV-ART-05 — HTML generation errors do not block JSON reports."""

    module = ModuleType("coverage")
    data_file = Path(".coverage")
    data_file.write_text("valid")
    payload = {"totals": {"percent_covered": 88.8}}

    class HTMLFailsCoverage:
        def __init__(self, data_file: str) -> None:
            self.data_file = data_file

        def load(self) -> None:
            return None

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: ["src/module.py"])

        def html_report(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("disk full")

        def json_report(self, outfile: str) -> None:
            Path(outfile).write_text(json.dumps(payload))

    module.Coverage = HTMLFailsCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.WARNING)

    rt._ensure_coverage_artifacts()

    assert "Failed to write coverage HTML report" in caplog.text
    assert coverage_test_environment.coverage_json.exists()
    assert json.loads(coverage_test_environment.coverage_json.read_text()) == payload
