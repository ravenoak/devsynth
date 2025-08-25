"""Validation utilities for MVUU metadata."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

import jsonschema

from .models import MVUU
from .parser import parse_commit_message
from .schema import MVUU_SCHEMA

CONVENTIONAL_RE = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([\w\-]+\))?: .+"
)


def validate_data(data: MVUU | Dict[str, Any]) -> MVUU:
    """Validate MVUU data against the JSON schema."""
    if isinstance(data, MVUU):
        payload = data.as_dict()
    else:
        payload = data
    jsonschema.validate(payload, MVUU_SCHEMA)
    return MVUU.from_dict(payload)


def validate_commit_message(message: str) -> MVUU:
    """Validate MVUU metadata contained in a commit message."""
    header = message.splitlines()[0]
    if not CONVENTIONAL_RE.match(header):
        raise ValueError("Commit header must follow Conventional Commits")
    mvuu = parse_commit_message(message)
    return validate_data(mvuu)


def validate_affected_files(mvuu: MVUU, changed_files: Iterable[str]) -> List[str]:
    """Return discrepancies between MVUU affected files and actual changes."""
    affected = set(mvuu.affected_files)
    changed = set(changed_files)
    errors: List[str] = []
    if affected != changed:
        missing = changed - affected
        extra = affected - changed
        if missing:
            errors.append(f"missing files: {sorted(missing)}")
        if extra:
            errors.append(f"extra files: {sorted(extra)}")
    return errors
