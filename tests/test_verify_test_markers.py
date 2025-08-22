import os
from pathlib import Path

import pytest

from scripts import verify_test_markers

# Importing ``verify_test_markers`` sets PYTEST_DISABLE_PLUGIN_AUTOLOAD; remove it
# so other tests can load their plugins normally.
os.environ.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)


@pytest.mark.fast
def test_parameterized_marker_counts(tmp_path, monkeypatch):
    """Ensure parameterized tests count markers once. ReqID: TEST-01"""
    test_file = tmp_path / "test_param.py"
    test_file.write_text(
        "import pytest\n\n"
        "@pytest.mark.fast\n"
        "@pytest.mark.parametrize('x', [1, 2, 3])\n"
        "def test_example(x):\n    pass\n"
    )
    monkeypatch.chdir(tmp_path)
    results = verify_test_markers.verify_file_markers(Path("test_param.py"))
    fast_info = results["recognized_markers"]["fast"]
    assert fast_info["file_count"] == 1
    assert fast_info["pytest_count"] == 1
    assert fast_info["recognized"] is True
