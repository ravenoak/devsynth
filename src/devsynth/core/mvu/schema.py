"""MVUU schema loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

# Repository root resolved from this file's location
ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "docs" / "specifications" / "mvuuschema.json"


def load_schema() -> dict[str, Any]:
    """Return the MVUU schema as a dictionary."""
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


MVUU_SCHEMA = load_schema()
