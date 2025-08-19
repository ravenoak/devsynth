"""Check release state against Git tags."""

from __future__ import annotations

import pathlib
import subprocess
import sys

import yaml

RELEASE_FILE = pathlib.Path("docs/release/0.1.0-alpha.1.md")


def parse_front_matter(path: pathlib.Path) -> dict:
    """Extract YAML front matter from a Markdown file."""
    text = path.read_text().splitlines()
    if text[0] != "---":
        return {}
    end = text[1:].index("---") + 1
    front_matter = "\n".join(text[1:end])
    return yaml.safe_load(front_matter) or {}


def tag_exists(tag: str) -> bool:
    """Return True if the given Git tag exists."""
    result = subprocess.run(
        [
            "git",
            "tag",
            "--list",
            tag,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def main() -> int:
    data = parse_front_matter(RELEASE_FILE)
    status = data.get("status")
    version = data.get("version")
    tag = f"v{version}" if version else None

    if status == "published" and tag and not tag_exists(tag):
        print(
            f"Release marked as published but Git tag {tag} is missing.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
