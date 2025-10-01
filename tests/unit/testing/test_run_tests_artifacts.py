from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture
def coverage_artifact_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> SimpleNamespace:
    """Configure run_tests coverage paths within a temporary directory."""

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
        data_file=tmp_path / ".coverage",
    )


@pytest.mark.fast
def test_reset_coverage_artifacts_removes_files_and_directories(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    env = coverage_artifact_environment
    env.data_file.write_text("payload")
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text("json")
    Path("coverage.json").write_text("legacy-json")
    env.html_dir.mkdir(parents=True, exist_ok=True)
    (env.html_dir / "index.html").write_text("html")
    env.legacy_dir.mkdir(parents=True, exist_ok=True)
    (env.legacy_dir / "index.html").write_text("legacy html")

    rt._reset_coverage_artifacts()

    assert not env.data_file.exists()
    assert not env.coverage_json.exists()
    assert not Path("coverage.json").exists()
    assert not env.html_dir.exists()
    assert not env.legacy_dir.exists()
    assert env.coverage_json.parent.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_warns_when_data_missing(
    coverage_artifact_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    module = ModuleType("coverage")

    class GuardCoverage:  # pragma: no cover - defensive guardrail
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("Coverage should not initialize without data file")

    module.Coverage = GuardCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.WARNING)

    rt._ensure_coverage_artifacts()

    assert "data file missing" in caplog.text
    assert not coverage_artifact_environment.coverage_json.exists()
    assert not coverage_artifact_environment.html_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_warns_when_no_measured_files(
    coverage_artifact_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    env = coverage_artifact_environment
    env.data_file.write_text("stub")

    module = ModuleType("coverage")

    class NoMeasuredCoverage:
        def __init__(self, data_file: str) -> None:
            self.data_file = data_file

        def load(self) -> None:
            return None

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: [])

        def html_report(
            self, *_args: object, **_kwargs: object
        ) -> None:  # pragma: no cover
            raise AssertionError("html_report should not be invoked")

        def json_report(
            self, *_args: object, **_kwargs: object
        ) -> None:  # pragma: no cover
            raise AssertionError("json_report should not be invoked")

    module.Coverage = NoMeasuredCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.WARNING)

    rt._ensure_coverage_artifacts()

    assert "no measured files" in caplog.text
    assert not env.coverage_json.exists()
    assert not env.html_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_generates_reports_and_syncs_legacy(
    coverage_artifact_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = coverage_artifact_environment
    env.data_file.write_text("valid")
    coverage_payload = {"totals": {"percent_covered": 99.9}}

    module = ModuleType("coverage")

    class SuccessfulCoverage:
        def __init__(self, data_file: str) -> None:
            self.data_file = data_file

        def load(self) -> None:
            return None

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

    env.legacy_dir.mkdir(parents=True, exist_ok=True)
    (env.legacy_dir / "stale.html").write_text("old")

    copytree_calls: list[tuple[Path, Path, dict[str, Any]]] = []
    copyfile_calls: list[tuple[Path, Path, dict[str, Any]]] = []

    def fake_copytree(
        src: str | Path, dst: str | Path, *args: object, **kwargs: Any
    ) -> Path:
        src_path = Path(src)
        dst_path = Path(dst)
        dst_path.mkdir(parents=True, exist_ok=True)
        for item in src_path.iterdir():
            if item.is_file():
                (dst_path / item.name).write_text(item.read_text())
        copytree_calls.append((src_path, dst_path, dict(kwargs)))
        return dst_path

    def fake_copyfile(
        src: str | Path, dst: str | Path, *args: object, **kwargs: Any
    ) -> str:
        src_path = Path(src)
        dst_path = Path(dst)
        dst_path.write_text(src_path.read_text())
        copyfile_calls.append((src_path, dst_path, dict(kwargs)))
        return str(dst_path)

    monkeypatch.setattr(rt.shutil, "copytree", fake_copytree)
    monkeypatch.setattr(rt.shutil, "copyfile", fake_copyfile)

    rt._ensure_coverage_artifacts()

    html_index = env.html_dir / "index.html"
    assert html_index.exists()
    assert html_index.read_text() == "<html>ok</html>"

    legacy_index = env.legacy_dir / "index.html"
    assert legacy_index.exists()
    assert legacy_index.read_text() == html_index.read_text()

    assert copytree_calls == [(env.html_dir, env.legacy_dir, {"dirs_exist_ok": True})]

    assert env.coverage_json.exists()
    assert json.loads(env.coverage_json.read_text()) == coverage_payload

    legacy_json = Path("coverage.json")
    assert legacy_json.exists()
    assert json.loads(legacy_json.read_text()) == coverage_payload

    assert copyfile_calls == [(env.coverage_json, legacy_json, {})]


@pytest.mark.fast
@pytest.mark.parametrize(
    ("initial_env", "expected_result", "expected_env"),
    [
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0"},
            False,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0"},
        ),
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "--no-cov -vv"},
            False,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "--no-cov -vv"},
        ),
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-p pytest_cov"},
            False,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-p pytest_cov"},
        ),
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-ppytest_cov"},
            False,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-ppytest_cov"},
        ),
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-vv"},
            True,
            {
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                "PYTEST_ADDOPTS": "-vv -p pytest_cov",
            },
        ),
        (
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
            True,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-p pytest_cov"},
        ),
    ],
)
def test_ensure_pytest_cov_plugin_env_cases(
    initial_env: dict[str, str], expected_result: bool, expected_env: dict[str, str]
) -> None:
    env = dict(initial_env)

    result = rt.ensure_pytest_cov_plugin_env(env)

    assert result is expected_result
    assert env == expected_env


@pytest.mark.fast
def test_coverage_artifacts_status_missing_json(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert (
        reason
        == f"Coverage JSON missing at {coverage_artifact_environment.coverage_json}"
    )


@pytest.mark.fast
def test_coverage_artifacts_status_invalid_json(
    coverage_artifact_environment: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text("{}")

    def fake_loads(_text: str) -> dict[str, Any]:
        raise json.JSONDecodeError("invalid", _text, 0)

    monkeypatch.setattr(rt.json, "loads", fake_loads)

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason and "Coverage JSON invalid" in reason


@pytest.mark.fast
def test_coverage_artifacts_status_missing_totals(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"other": 1}))

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason == "Coverage JSON missing totals.percent_covered"


@pytest.mark.fast
def test_coverage_artifacts_status_missing_html(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason == f"Coverage HTML missing at {env.html_dir / 'index.html'}"


@pytest.mark.fast
def test_coverage_artifacts_status_html_indicates_no_data(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))
    env.html_dir.mkdir(parents=True, exist_ok=True)
    (env.html_dir / "index.html").write_text("No coverage data available")

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason == "Coverage HTML indicates no recorded data"


@pytest.mark.fast
def test_coverage_artifacts_status_html_read_error(
    coverage_artifact_environment: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))
    env.html_dir.mkdir(parents=True, exist_ok=True)
    html_index = env.html_dir / "index.html"
    html_index.write_text("<html>ok</html>")

    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args: object, **kwargs: Any) -> str:
        if self == html_index:
            raise OSError("unreadable")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason and "Coverage HTML unreadable" in reason


@pytest.mark.fast
def test_coverage_artifacts_status_success(
    coverage_artifact_environment: SimpleNamespace,
) -> None:
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"totals": {"percent_covered": 92.5}}))
    env.html_dir.mkdir(parents=True, exist_ok=True)
    (env.html_dir / "index.html").write_text("<html>ok</html>")

    ok, reason = rt.coverage_artifacts_status()

    assert ok
    assert reason is None


@pytest.mark.fast
def test_enforce_coverage_threshold_success(tmp_path: Path) -> None:
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps({"totals": {"percent_covered": 95.0}}))

    result = rt.enforce_coverage_threshold(coverage_file, minimum_percent=90.0)

    assert result == pytest.approx(95.0)


@pytest.mark.fast
def test_enforce_coverage_threshold_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(missing, exit_on_failure=False)

    assert str(missing) in str(excinfo.value)


@pytest.mark.fast
def test_enforce_coverage_threshold_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text("invalid")

    def fake_loads(_text: str) -> dict[str, Any]:
        raise json.JSONDecodeError("invalid", _text, 0)

    monkeypatch.setattr(rt.json, "loads", fake_loads)

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(coverage_file, exit_on_failure=False)

    assert "Coverage JSON" in str(excinfo.value)


@pytest.mark.fast
def test_enforce_coverage_threshold_missing_percent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text("{}")

    monkeypatch.setattr(rt.json, "loads", lambda _text: {"totals": {}})

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(coverage_file, exit_on_failure=False)

    assert "totals.percent_covered" in str(excinfo.value)


@pytest.mark.fast
def test_enforce_coverage_threshold_below_minimum(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text("{}")

    monkeypatch.setattr(
        rt.json,
        "loads",
        lambda _text: {"totals": {"percent_covered": 75.0}},
    )

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(
            coverage_file, minimum_percent=90.0, exit_on_failure=False
        )

    assert "below the required" in str(excinfo.value)
