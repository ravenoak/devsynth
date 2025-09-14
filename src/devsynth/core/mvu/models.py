"""Data models for MVUU metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MVUU:
    """Dataclass representing MVUU metadata."""

    utility_statement: str
    affected_files: list[str]
    tests: list[str]
    TraceID: str
    mvuu: bool
    issue: str
    notes: str | None = None
    issue_title: str | None = None
    acceptance_criteria: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MVUU:
        """Create an MVUU instance from a dictionary."""
        return cls(**data)

    def as_dict(self) -> dict[str, Any]:
        """Return metadata as a dictionary."""
        data: dict[str, Any] = {
            "utility_statement": self.utility_statement,
            "affected_files": self.affected_files,
            "tests": self.tests,
            "TraceID": self.TraceID,
            "mvuu": self.mvuu,
            "issue": self.issue,
        }
        if self.notes is not None:
            data["notes"] = self.notes
        return data
