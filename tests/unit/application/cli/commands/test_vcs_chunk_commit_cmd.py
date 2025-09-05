import pytest

from devsynth.application.cli.commands.vcs_chunk_commit_cmd import (
    generate_message,
    group_changes,
)


@pytest.mark.fast
def test_group_changes_categorizes_and_orders() -> None:
    paths = [
        "README.md",
        "docs/guide.md",
        "tests/unit/test_something.py",
        "src/devsynth/module.py",
        "pyproject.toml",
        "scripts/util.sh",
        ".github/workflows/ci.yml",
        "examples/demo.py",
        "templates/page.html",
        "misc/other.txt",
    ]

    groups = group_changes(paths)

    # Expected category order
    expected_order = [
        "docs",
        "tests",
        "src",
        "config",
        "scripts",
        "ci",
        "examples",
        "templates",
        "chore",
    ]
    assert [g.category for g in groups] == [
        c for c in expected_order if any(g.category == c for g in groups)
    ]

    # Spot-check grouping
    by_cat = {g.category: set(g.files) for g in groups}
    assert "README.md" in by_cat["docs"]
    assert "docs/guide.md" in by_cat["docs"]
    assert "tests/unit/test_something.py" in by_cat["tests"]
    assert "src/devsynth/module.py" in by_cat["src"]
    assert "pyproject.toml" in by_cat["config"]
    assert "scripts/util.sh" in by_cat["scripts"]
    assert ".github/workflows/ci.yml" in by_cat["ci"]
    assert "examples/demo.py" in by_cat["examples"]
    assert "templates/page.html" in by_cat["templates"]
    assert "misc/other.txt" in by_cat["chore"]


@pytest.mark.fast
def test_generate_message_includes_rationale_and_files() -> None:
    files = ["src/a.py", "src/b.py", "src/c.py", "src/d.py", "src/e.py", "src/f.py"]
    msg = generate_message("src", files)

    # Title and file count
    assert msg.splitlines()[0].startswith("src: update 6 file(s)")

    # Includes sample of files
    assert "src/a.py" in msg and "src/e.py" in msg

    # Includes Socratic and Dialectical rationale
    assert "Socratic" in msg
    assert "Dialectical" in msg
