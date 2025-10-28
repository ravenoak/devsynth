"""Utilities for reprioritizing open issues based on milestone."""

from __future__ import annotations

import pathlib
from typing import Dict

ISSUES_DIR = pathlib.Path("issues")

PRIORITY_MAP = {
    "phase 1": "high",
    "phase 2": "medium",
}


def reprioritize_open_issues(issues_dir: pathlib.Path = ISSUES_DIR) -> dict[str, int]:
    """Update issue priorities according to milestone.

    Args:
        issues_dir: Directory containing issue markdown files.

    Returns:
        Counts of issues updated for each priority level.
    """
    counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for path in issues_dir.glob("*.md"):
        if path.name in {"README.md", "TEMPLATE.md"}:
            continue
        lines = path.read_text().splitlines()
        milestone = None
        priority_idx = None
        for i, line in enumerate(lines):
            if line.lower().startswith("milestone:"):
                milestone = line.split(":", 1)[1].strip().lower()
            elif line.lower().startswith("priority:"):
                priority_idx = i
        if milestone is None or priority_idx is None:
            continue
        new_priority = PRIORITY_MAP.get(milestone, "low")
        lines[priority_idx] = f"Priority: {new_priority}"
        path.write_text("\n".join(lines) + "\n")
        counts[new_priority] += 1
    return counts
