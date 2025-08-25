"""Data models for MVUU metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MVUU:
    """Dataclass representing MVUU metadata."""

    utility_statement: str
    affected_files: List[str]
    tests: List[str]
    TraceID: str
    mvuu: bool
    issue: str
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MVUU":
        """Create an MVUU instance from a dictionary."""
        return cls(**data)

    def as_dict(self) -> Dict[str, Any]:
        """Return metadata as a dictionary."""
        data: Dict[str, Any] = {
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
