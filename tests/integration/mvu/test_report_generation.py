from __future__ import annotations

# Load the command module directly to avoid package side effects
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import click
import pytest
import typer
from typer.testing import CliRunner

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "mvu_report_cmd.py"
)
spec = importlib.util.spec_from_file_location("mvu_report_cmd", MODULE_PATH)
mvu_module = importlib.util.module_from_spec(spec)
sys.modules["mvu_report_cmd"] = mvu_module
assert spec.loader is not None
spec.loader.exec_module(mvu_module)
mvu_report_cmd = mvu_module.mvu_report_cmd


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types."""
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        try:
            return orig(annotation=annotation, parameter_info=parameter_info)
        except Exception:
            return click.STRING

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


def _write_commit(path: Path, message: str) -> None:
    subprocess.run(["git", "add", path.name], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)


def _mvuu_message(trace_id: str, file_name: str) -> str:
    data = {
        "utility_statement": f"Add {file_name}",
        "affected_files": [file_name],
        "tests": ["pytest"],
        "TraceID": trace_id,
        "mvuu": True,
        "issue": trace_id,
    }
    return "feat: add\n\n```json\n" + json.dumps(data, indent=2) + "\n```"


def test_report_generation(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    file1 = repo / "one.txt"
    file1.write_text("1", encoding="utf-8")
    _write_commit(file1, _mvuu_message("DSY-0001", "one.txt"))

    file2 = repo / "two.txt"
    file2.write_text("2", encoding="utf-8")
    _write_commit(file2, _mvuu_message("DSY-0002", "two.txt"))

    runner = CliRunner()
    app = typer.Typer()
    mvu_app = typer.Typer()
    mvu_app.command("report")(mvu_report_cmd)
    app.add_typer(mvu_app, name="mvu")

    result = runner.invoke(app, ["mvu", "report", "--format", "markdown"])
    assert result.exit_code == 0
    assert "| TraceID |" in result.stdout
    assert "DSY-0001" in result.stdout

    html_file = repo / "report.html"
    result = runner.invoke(
        app,
        ["mvu", "report", "--format", "html", "--output", str(html_file)],
    )
    assert result.exit_code == 0
    html = html_file.read_text(encoding="utf-8")
    assert "<table>" in html and "DSY-0002" in html
