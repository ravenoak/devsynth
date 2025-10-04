from __future__ import annotations

import logging
from pathlib import Path

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_ensure_coverage_artifacts_short_circuits_without_measured_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    coverage_stub_factory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Skip artifact generation when coverage data reports no measured files."""

    monkeypatch.chdir(tmp_path)
    coverage_json = tmp_path / "reports" / "coverage.json"
    html_dir = tmp_path / "reports" / "html"
    legacy_dir = tmp_path / "legacy" / "html"

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", coverage_json)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(rt, "LEGACY_HTML_DIRS", (legacy_dir,))

    data_file = tmp_path / ".coverage"
    data_file.write_text("stub data")

    stub = coverage_stub_factory(measured_files=[])

    with caplog.at_level(logging.WARNING, logger="devsynth.testing.run_tests"):
        rt._ensure_coverage_artifacts()

    assert "no measured files" in caplog.text
    assert not coverage_json.exists()
    assert not html_dir.exists()
    assert not legacy_dir.exists()
    assert stub.html_calls == []
    assert stub.json_calls == []
    assert len(stub.instances) == 1
    assert Path(stub.instances[0].data_file).resolve() == data_file.resolve()
