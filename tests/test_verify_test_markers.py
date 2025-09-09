import os
from pathlib import Path

import pytest

from scripts import verify_test_markers

# Importing ``verify_test_markers`` sets PYTEST_DISABLE_PLUGIN_AUTOLOAD; remove it
# so other tests can load their plugins normally.
os.environ.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)


@pytest.mark.fast
def test_parameterized_marker_counts(tmp_path, monkeypatch):
    """Ensure parameterized tests count markers once.
    Issue: issues/Expand-test-generation-capabilities.md ReqID: FR-01"""
    test_file = tmp_path / "test_param.py"
    test_file.write_text(
        "import pytest\n\n"
        "@pytest.mark.fast\n"
        "@pytest.mark.parametrize('x', [1, 2, 3])\n"
        "def test_example(x):\n    pass\n"
    )
    monkeypatch.chdir(tmp_path)
    results = verify_test_markers.verify_files([Path("test_param.py")])
    file_result = results["files"][str((tmp_path / "test_param.py").resolve())]
    assert file_result["markers"].get("fast") == 1


@pytest.mark.fast
def test_reports_collection_errors(tmp_path, monkeypatch):
    """Syntax issues are surfaced with file context.
    Issue: issues/Expand-test-generation-capabilities.md ReqID: FR-02"""
    bad_file = tmp_path / "test_bad.py"
    bad_file.write_text(
        "import pytest\nimport non_existent_module\n\n"
        "@pytest.mark.fast\n"
        "def test_example():\n    pass\n"
    )
    monkeypatch.chdir(tmp_path)
    results = verify_test_markers.verify_files([bad_file])
    file_result = results["files"][str(bad_file.resolve())]
    assert any(issue["type"] == "collection_error" for issue in file_result["issues"])
