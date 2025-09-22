import json
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture
def coverage_fragment_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> SimpleNamespace:
    """Redirect coverage artifact paths into a temporary directory."""

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
def test_ensure_coverage_artifacts_combines_fragment_files(
    coverage_fragment_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: COV-ART-05 — Fragment files consolidate before artifact generation."""

    module = ModuleType("coverage")
    fragments = [Path(".coverage.alpha"), Path(".coverage.beta")]
    for fragment in fragments:
        fragment.write_text("fragment")

    class FragmentCoverage:
        instances: list["FragmentCoverage"] = []

        def __init__(self, data_file: str) -> None:  # noqa: D401 - test stub
            self.data_file = data_file
            self.combine_args: list[str] | None = None
            self.save_called = False
            self.load_called = False
            self.html_report_called = False
            self.json_report_called = False
            FragmentCoverage.instances.append(self)

        def combine(self, paths: list[str]) -> None:
            self.combine_args = list(paths)

        def save(self) -> None:
            Path(self.data_file).write_text("combined")
            self.save_called = True

        def load(self) -> None:
            self.load_called = True

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(
                measured_files=lambda: ["src/devsynth/example.py"],
            )

        def html_report(self, directory: str) -> None:
            self.html_report_called = True
            output_dir = Path(directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "index.html").write_text("<html>ok</html>")

        def json_report(self, outfile: str) -> None:
            self.json_report_called = True
            output_path = Path(outfile)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps({"totals": {"percent_covered": 99.9}})
            )

    module.Coverage = FragmentCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", module)

    caplog.set_level(logging.INFO, logger="devsynth.testing.run_tests")

    rt._ensure_coverage_artifacts()

    assert Path(".coverage").exists(), "Combined coverage file should be created"
    assert not any(fragment.exists() for fragment in fragments)

    assert FragmentCoverage.instances, "Coverage should be instantiated"
    combine_instance = FragmentCoverage.instances[0]
    expected_fragment_paths = [str(f.resolve()) for f in fragments]
    assert combine_instance.combine_args == expected_fragment_paths
    assert combine_instance.save_called is True

    assert len(FragmentCoverage.instances) >= 2
    execution_instance = FragmentCoverage.instances[-1]
    assert execution_instance.load_called is True
    assert execution_instance.html_report_called is True
    assert execution_instance.json_report_called is True

    env = coverage_fragment_environment
    html_index = env.html_dir / "index.html"
    legacy_index = env.legacy_dir / "index.html"
    assert env.coverage_json.exists()
    assert html_index.exists()
    assert legacy_index.exists()
    assert "Consolidated" in caplog.text
