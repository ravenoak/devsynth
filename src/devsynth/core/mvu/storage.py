"""Storage helpers for MVUU metadata."""

from __future__ import annotations

import json
import subprocess
from typing import Optional

from .models import MVUU
from .parser import parse_commit_message


def format_mvuu_footer(mvuu: MVUU) -> str:
    """Return a canonical commit message footer for MVUU metadata."""
    return "```json\n" + json.dumps(mvuu.as_dict(), indent=2) + "\n```"


def read_commit_message(commit: str) -> str:
    """Return the commit message for a given commit hash."""
    return subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B", commit], text=True
    )


def read_mvuu_from_commit(commit: str) -> Optional[MVUU]:
    """Return MVUU metadata embedded in a commit message."""
    try:
        message = read_commit_message(commit)
        return parse_commit_message(message)
    except Exception:
        return None


def append_mvuu_footer(message: str, mvuu: MVUU) -> str:
    """Append MVUU metadata to a commit message."""
    footer = format_mvuu_footer(mvuu)
    if message.endswith("\n"):
        return message + footer + "\n"
    return message + "\n" + footer + "\n"


def read_note(commit: str) -> Optional[MVUU]:
    """Read MVUU metadata from a git note if present."""
    try:
        note = subprocess.check_output(
            ["git", "notes", "show", commit], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return None
    if not note:
        return None
    data = json.loads(note)
    return MVUU.from_dict(data)


def write_note(commit: str, mvuu: MVUU) -> None:
    """Write MVUU metadata to a git note."""
    json_data = json.dumps(mvuu.as_dict(), indent=2)
    subprocess.check_call(["git", "notes", "add", "-f", "-m", json_data, commit])
