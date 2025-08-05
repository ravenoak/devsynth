"""Parsing helpers for MVUU metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .models import MVUU

JSON_FENCE_RE = re.compile(r"```(?:json|yaml)\n(.*?)\n```", re.DOTALL)


def parse_commit_message(message: str) -> MVUU:
    """Extract MVUU metadata from a commit message."""
    match = JSON_FENCE_RE.search(message)
    if not match:
        raise ValueError("Missing MVUU block fenced with ```json ... ```")
    block = match.group(1)
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        data = yaml.safe_load(block)
    if not isinstance(data, dict):
        raise ValueError("MVUU block does not contain an object")
    return MVUU.from_dict(data)


def parse_file(path: Path) -> MVUU:
    """Load MVUU metadata from a JSON or YAML file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        data: Any = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("MVUU file must contain a JSON/YAML object")
    return MVUU.from_dict(data)
