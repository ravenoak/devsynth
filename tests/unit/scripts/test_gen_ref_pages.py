import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.fast
def test_gen_ref_pages_matches_examples(tmp_path: Path) -> None:
    """gen_ref_pages should reproduce example output."""
    pytest.importorskip("mkdocs_gen_files")
    # Setup minimal project structure
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    repo_root = Path(__file__).resolve().parents[3]
    shutil.copy(
        repo_root / "scripts" / "gen_ref_pages.py", scripts_dir / "gen_ref_pages.py"
    )

    src_pkg = tmp_path / "src" / "devsynth"
    src_pkg.mkdir(parents=True)
    (src_pkg / "__init__.py").write_text("\n")
    (src_pkg / "api.py").write_text("\n")

    (tmp_path / "mkdocs.yml").write_text("site_name: example\n")
    (tmp_path / "docs").mkdir()

    subprocess.run(
        [sys.executable, str(scripts_dir / "gen_ref_pages.py")],
        cwd=tmp_path,
        check=True,
    )

    generated = tmp_path / "docs" / "api_reference"
    example = repo_root / "docs" / "api_reference"

    assert (generated / "devsynth" / "index.md").read_text() == (
        example / "devsynth" / "index.md"
    ).read_text()
    assert (generated / "devsynth" / "api.md").read_text() == (
        example / "devsynth" / "api.md"
    ).read_text()
    assert (generated / "SUMMARY.md").read_text() == (
        example / "SUMMARY.md"
    ).read_text()
