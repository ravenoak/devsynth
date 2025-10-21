"""Shared helpers for run_tests unit tests that exercise typed metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Iterable, Sequence

import devsynth.testing.run_tests as rt

_DEFAULT_STARTED_AT = datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat()
_DEFAULT_COMPLETED_AT = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc).isoformat()


def build_batch_metadata(
    metadata_id: str,
    *,
    command: Iterable[str] | None = None,
    returncode: int = 0,
    coverage_enabled: bool = True,
    dry_run: bool | None = None,
    coverage_issue: str | None = None,
) -> rt.BatchExecutionMetadata:
    """Create a minimally valid batch metadata object for tests."""

    normalized_command = tuple(command or ("python", "-m", "pytest"))
    metadata: rt.BatchExecutionMetadata = {
        "metadata_id": metadata_id,
        "command": normalized_command,
        "returncode": returncode,
        "started_at": _DEFAULT_STARTED_AT,
        "completed_at": _DEFAULT_COMPLETED_AT,
        "coverage_enabled": coverage_enabled,
    }
    if dry_run is not None:
        metadata["dry_run"] = dry_run
    if coverage_issue is not None:
        metadata["coverage_issue"] = coverage_issue
    return metadata


def build_segment_metadata(
    metadata_id: str,
    *,
    segments: Sequence[rt.BatchExecutionMetadata] | None = None,
    commands: Sequence[Sequence[str]] | None = None,
    returncode: int = 0,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> rt.SegmentedRunMetadata:
    """Create aggregated metadata for segmented executions."""

    actual_segments: tuple[rt.BatchExecutionMetadata, ...] = (
        tuple(segments)
        if segments is not None
        else tuple()
    )
    if commands is not None:
        normalized_commands = tuple(tuple(command) for command in commands)
    else:
        normalized_commands = tuple(meta["command"] for meta in actual_segments)
    return {
        "metadata_id": metadata_id,
        "commands": normalized_commands,
        "returncode": returncode,
        "started_at": started_at or _DEFAULT_STARTED_AT,
        "completed_at": completed_at or _DEFAULT_COMPLETED_AT,
        "segments": actual_segments,
    }
