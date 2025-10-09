import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.fast]

sys.path.append("scripts")

from check_internal_links import check_internal_links  # type: ignore


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_check_internal_links_with_valid_anchor(tmp_path):
    """Links with valid anchors should not be reported as broken."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    _write(docs_dir / "target.md", "# Section Title\n")
    source = _write(docs_dir / "source.md", "[Link](target.md#section-title)\n")

    broken = check_internal_links(source, docs_dir)

    assert broken == []


def test_check_internal_links_with_missing_anchor(tmp_path):
    """Links with missing anchors should be reported as broken."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    _write(docs_dir / "target.md", "# Section Title\n")
    source = _write(docs_dir / "source.md", "[Link](target.md#missing)\n")

    broken = check_internal_links(source, docs_dir)

    assert broken
    assert broken[0]["url"] == "target.md#missing"
