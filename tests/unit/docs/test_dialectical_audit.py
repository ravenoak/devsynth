import json
from pathlib import Path

import pytest

from scripts import dialectical_audit as da


@pytest.mark.fast
def test_fails_when_feature_in_tests_but_not_docs(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    root = tmp_path
    docs = root / "docs"
    tests_dir = root / "tests"
    src = root / "src"
    docs.mkdir()
    tests_dir.mkdir()
    src.mkdir()

    (tests_dir / "feature.feature").write_text(
        "Feature: Undocumented Feature\n",
        encoding="utf-8",
    )
    (src / "impl.py").write_text(
        "# Feature: Undocumented Feature\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(da, "ROOT", root)
    monkeypatch.setattr(da, "DOCS", docs)
    monkeypatch.setattr(da, "TESTS", tests_dir)
    monkeypatch.setattr(da, "SRC", src)
    log_path = root / "dialectical_audit.log"
    monkeypatch.setattr(da, "LOG_PATH", log_path)

    exit_code = da.main()
    assert exit_code == 1

    data = json.loads(log_path.read_text())
    assert (
        "Feature 'Undocumented Feature' has tests but is not documented."
        in data["questions"]
    )


@pytest.mark.fast
def test_fails_when_feature_in_docs_but_not_tests(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    root = tmp_path
    docs = root / "docs"
    tests_dir = root / "tests"
    src = root / "src"
    docs.mkdir()
    tests_dir.mkdir()
    src.mkdir()

    (docs / "feature.md").write_text(
        "Feature: Untested Feature\n",
        encoding="utf-8",
    )
    (src / "impl.py").write_text(
        "# Feature: Untested Feature\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(da, "ROOT", root)
    monkeypatch.setattr(da, "DOCS", docs)
    monkeypatch.setattr(da, "TESTS", tests_dir)
    monkeypatch.setattr(da, "SRC", src)
    log_path = root / "dialectical_audit.log"
    monkeypatch.setattr(da, "LOG_PATH", log_path)

    exit_code = da.main()
    assert exit_code == 1

    data = json.loads(log_path.read_text())
    assert (
        "Feature 'Untested Feature' is documented but has no corresponding tests."
        in data["questions"]
    )
