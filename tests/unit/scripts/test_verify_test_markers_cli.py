import builtins
import importlib
import pathlib
import types

import pytest


def test_argparser_includes_changed_flag():
    mod = importlib.import_module("scripts.verify_test_markers")
    parser = mod.get_arg_parser()
    help_text = parser.format_help()
    assert "--changed" in help_text
    assert "--base-ref" in help_text


def test_verify_files_with_temp_test(tmp_path: pathlib.Path):
    # Create a simple test file with a marker
    p = tmp_path / "test_sample.py"
    p.write_text(
        """
import pytest

@pytest.mark.unit
class TestDemo:
    def test_ok(self):
        assert 1 + 1 == 2
""",
        encoding="utf-8",
    )

    mod = importlib.import_module("scripts.verify_test_markers")
    result = mod.verify_files([p])
    assert isinstance(result, dict)
    assert len(result.get("files", {})) == 1
    # Marker summary written to report; per-file markers accessible via result["files"][...]
    file_data = next(iter(result["files"].values()))
    assert "markers" in file_data
    assert file_data["markers"].get("unit", 0) >= 1
