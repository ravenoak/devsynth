"""Regression test ensuring documentation builds successfully."""

import os
import pathlib
import shutil
import subprocess

import pytest


@pytest.mark.fast
def test_docs_build(tmp_path):
    """Docs build without errors using MkDocs."""
    pytest.importorskip("mkdocs")
    pytest.importorskip("material")
    if shutil.which("mkdocs") is None:
        pytest.skip("mkdocs command not found")

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    tmp_config = tmp_path / "mkdocs.yml"
    tmp_config.write_text(
        "\n".join(
            [
                f"INHERIT: {repo_root / 'mkdocs.yml'}",
                f"docs_dir: {repo_root / 'docs'}",
                f"site_dir: {tmp_path / 'site'}",
                "plugins:",
                "  - search",
                "  - literate-nav:",
                "      nav_file: SUMMARY.md",
                "  - gen-files:",
                "      scripts:",
                f"        - {repo_root / 'scripts/gen_ref_pages.py'}",
                "  - include-markdown",
            ]
        )
    )
    result = subprocess.run(
        [
            "poetry",
            "run",
            "mkdocs",
            "build",
            "--strict",
            "--quiet",
            "-f",
            str(tmp_config),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
