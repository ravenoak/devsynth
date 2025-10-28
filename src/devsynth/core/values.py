from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections.abc import Iterable

import yaml


@dataclass
class CoreValues:
    """Project core values loaded from a YAML file."""

    statements: list[str] = field(default_factory=list)

    def add_value(self, value: str) -> None:
        """Add a value to ``statements`` if not already present."""
        value = str(value).strip()
        if value and value not in self.statements:
            self.statements.append(value)

    def update_values(self, values: Iterable[str]) -> None:
        """Replace ``statements`` with the given values, ensuring uniqueness."""
        self.statements = []
        for val in values:
            self.add_value(val)

    def validate_report(self, report: dict[str, Any]) -> list[str]:
        """Return any value conflicts found within ``report``."""
        return check_report_for_value_conflicts(report, self)

    @classmethod
    def load(cls, start_path: str | Path | None = None) -> CoreValues:
        """Load values from ``.devsynth/values.yml``.

        Parameters
        ----------
        start_path:
            Optional base directory to search from. Defaults to the current
            working directory.
        """
        root = Path(start_path or os.getcwd())
        values_file = root / ".devsynth" / "values.yml"
        if not values_file.exists():
            return cls()
        with open(values_file) as f:
            data = yaml.safe_load(f) or []
        if isinstance(data, dict):
            statements = list(data.get("values", []))
        elif isinstance(data, Iterable):
            statements = list(data)
        else:
            statements = []
        statements = [str(s) for s in statements]
        return cls(statements)


def _collect_text(obj: Any, parts: list[str]) -> None:
    if isinstance(obj, str):
        parts.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            _collect_text(value, parts)
    elif isinstance(obj, list):
        for item in obj:
            _collect_text(item, parts)


def find_value_conflicts(text: str, core_values: CoreValues) -> list[str]:
    """Return values that appear contradicted in the given text."""
    conflicts: list[str] = []
    lowered = text.lower()
    for val in core_values.statements:
        v = val.lower()
        tokens = [f"not {v}", f"no {v}", f"against {v}", f"violate {v}"]
        if any(t in lowered for t in tokens):
            conflicts.append(val)
    return conflicts


def check_report_for_value_conflicts(
    report: dict[str, Any], core_values: CoreValues
) -> list[str]:
    """Check a report structure for conflicts with the given values."""
    text_parts: list[str] = []
    _collect_text(report, text_parts)
    combined = " ".join(text_parts)
    return find_value_conflicts(combined, core_values)
