"""Tests for the :mod:`repo_analyzer` module."""

import contextlib
import io
import json
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.repo_analyzer import RepoAnalyzer


class TestRepoAnalyzer:
    """Unit tests for :class:`RepoAnalyzer`."""

    @pytest.mark.medium
    def test_analyze_maps_dependencies_and_structure(self) -> None:
        """Ensure dependencies and structure are correctly mapped."""

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("import b\n")
            (root / "b.py").write_text("x = 1\n")
            (root / "sub").mkdir()
            (root / "sub" / "c.py").write_text("from a import something\n")

            analyzer = RepoAnalyzer(tmpdir)
            result = analyzer.analyze()

            assert result["dependencies"]["a.py"] == ["b"]
            assert result["dependencies"]["sub/c.py"] == ["a"]
            structure = result["structure"]
            assert set(structure["."]) == {"a.py", "b.py", "sub"}
            assert "c.py" in structure["sub"]

    @pytest.mark.medium
    def test_cli_entry_invokes_repo_analyzer(self, monkeypatch) -> None:
        """Verify ``--analyze-repo`` uses the RepoAnalyzer and prints JSON."""

        fake_result = {"dependencies": {}, "structure": {}}
        analyze_mock = MagicMock(return_value=fake_result)
        monkeypatch.setattr(
            "devsynth.application.code_analysis.repo_analyzer.RepoAnalyzer.analyze",
            analyze_mock,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            argv = ["devsynth", "--analyze-repo", tmpdir]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                old_argv = sys.argv
                sys.argv = argv
                try:
                    runpy.run_module("devsynth.cli", run_name="__main__")
                except SystemExit:
                    pass
                finally:
                    sys.argv = old_argv

        assert "devsynth.adapters.cli.typer_adapter" not in sys.modules
        analyze_mock.assert_called_once()
        assert json.loads(buf.getvalue()) == fake_result

