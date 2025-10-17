"""Run strict mypy and publish release evidence manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from devsynth.release import publish_manifest as _publish_manifest_type
else:
    # Handle circular import by making publish_manifest optional
    publish_manifest: Optional[Any] = None

try:
    from devsynth.release import (
        publish_manifest,
    )
except ImportError:
    # publish_manifest remains None on import failure
    pass


def compute_file_checksum(path: Path) -> str:
    """Return the SHA-256 checksum for ``path`` contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_release_tag(default: str = "unknown") -> str:
    """Determine the active release tag.

    The helper first honours ``DEVSYNTH_RELEASE_TAG`` for operator overrides and
    falls back to the Poetry project version recorded in ``pyproject.toml``.
    """
    # Check environment variable override
    env_tag = os.environ.get("DEVSYNTH_RELEASE_TAG")
    if env_tag:
        return str(env_tag)

    # Fall back to pyproject.toml version
    try:
        import tomllib
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
                version = data.get("project", {}).get("version", default)
                return str(version) if version is not None else default
    except (ImportError, FileNotFoundError, tomllib.TOMLDecodeError):
        pass

    return default


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Write ``manifest`` to ``path`` with pretty JSON formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")


def _coerce_sequence(value: object) -> Sequence[object]:
    """Return ``value`` as a safe sequence for iteration."""

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _build_inventory_markdown(
    *,
    combined_output: str,
    timestamp: str,
    exit_code: int,
    release_tag: str,
) -> tuple[str, int]:
    """Create a strict mypy inventory summary."""

    error_counts: defaultdict[str, int] = defaultdict(int)
    pattern = re.compile(r"^(?P<path>[^:]+):\d+:\d+: error:")
    for line in combined_output.splitlines():
        match = pattern.match(line)
        if match:
            error_counts[match.group("path")] += 1

    total_errors = sum(error_counts.values())
    lines: list[str] = [
        f"# Strict mypy inventory ({timestamp})",
        "",
        f"- Release tag: `{release_tag}`",
        f"- Exit code: `{exit_code}`",
        f"- Total errors: `{total_errors}`",
        "",
        "| Path | Errors |",
        "| --- | ---: |",
    ]

    for path in sorted(error_counts):
        lines.append(f"| `{path}` | {error_counts[path]} |")

    if not error_counts:
        lines.append("| _no strict errors reported_ | 0 |")

    return "\n".join(lines) + "\n", total_errors


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help=(
            "Additional arguments forwarded to mypy after '--'. "
            "Example: python -m devsynth.testing.mypy_strict_runner -- --config-file custom.ini"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    extra_args = list(args.extra or [])
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "src/devsynth",
        *extra_args,
    ]

    started_at = datetime.now(UTC)
    process = subprocess.run(cmd, capture_output=True, text=True)
    completed_at = datetime.now(UTC)

    stdout = process.stdout or ""
    stderr = process.stderr or ""
    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)
    combined_output = stdout + ("\n" + stderr if stderr and stdout else stderr)

    timestamp = completed_at.strftime("%Y%m%dT%H%M%SZ")
    diagnostics_dir = Path("diagnostics")
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    log_path = diagnostics_dir / f"mypy_strict_src_devsynth_{timestamp}.txt"
    log_path.write_text(combined_output)

    release_tag = get_release_tag()
    inventory_markdown, error_count = _build_inventory_markdown(
        combined_output=combined_output,
        timestamp=timestamp,
        exit_code=process.returncode,
        release_tag=release_tag,
    )
    inventory_path = diagnostics_dir / f"mypy_strict_inventory_{timestamp}.md"
    inventory_path.write_text(inventory_markdown)

    log_checksum = compute_file_checksum(log_path)
    inventory_checksum = compute_file_checksum(inventory_path)

    run_checksum_builder = hashlib.sha256()
    run_checksum_builder.update(str(process.returncode).encode("utf-8"))
    run_checksum_builder.update(str(error_count).encode("utf-8"))
    run_checksum_builder.update(log_checksum.encode("utf-8"))
    run_checksum_builder.update(inventory_checksum.encode("utf-8"))
    run_checksum = run_checksum_builder.hexdigest()

    manifest = {
        "run_type": "typing",
        "release_tag": release_tag,
        "source_command": " ".join(cmd),
        "artifacts": [
            {
                "artifact_type": "mypy_log",
                "path": str(log_path),
                "checksum": log_checksum,
                "collected_at": completed_at.isoformat(),
            },
            {
                "artifact_type": "mypy_inventory",
                "path": str(inventory_path),
                "checksum": inventory_checksum,
                "collected_at": completed_at.isoformat(),
            },
        ],
        "test_run": {
            "profile": "typing-strict",
            "coverage_percent": None,
            "tests_collected": None,
            "exit_code": process.returncode,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "run_checksum": run_checksum,
            "metadata": {
                "error_count": error_count,
            },
        },
        "quality_gate": {
            "gate_name": "typing",
            "threshold": 0.0,
            "status": "pass" if process.returncode == 0 else "fail",
            "evaluated_at": completed_at.isoformat(),
            "metadata": {
                "error_count": error_count,
            },
        },
    }

    manifest_path = diagnostics_dir / f"mypy_strict_manifest_{timestamp}.json"
    latest_manifest_path = diagnostics_dir / "mypy_strict_manifest_latest.json"
    write_manifest(manifest_path, manifest)
    write_manifest(latest_manifest_path, manifest)

    # Handle publication logic with proper None checking
    publication_success = False
    if publish_manifest is not None:
        try:
            publication = publish_manifest(manifest)
            evidence_created = _coerce_sequence(publication.created.get("release_evidence"))
            evidence_parts = []
            for evidence_id, created in zip(publication.evidence_ids, evidence_created):
                suffix = " (new)" if bool(created) else ""
                evidence_parts.append(f"{evidence_id}{suffix}")
            evidence_summary = ", ".join(evidence_parts) or "none"
            test_run_state = (
                "new" if bool(publication.created.get("test_run")) else "updated"
            )
            gate_state = (
                "new" if bool(publication.created.get("quality_gate")) else "updated"
            )
            print(
                "[knowledge-graph] typing gate "
                f"{publication.gate_status} → QualityGate {publication.quality_gate_id} ({gate_state}), "
                f"TestRun {publication.test_run_id} ({test_run_state}), Evidence [{evidence_summary}] via "
                f"{publication.adapter_backend}; errors={error_count}"
            )
            publication_success = True
        except Exception as exc:
            print(f"[knowledge-graph] typing ingestion failed: {exc}", file=sys.stderr)

    if not publication_success:
        print(f"[knowledge-graph] typing manifest created but knowledge graph unavailable (circular import); errors={error_count}", file=sys.stderr)

    return process.returncode


if __name__ == "__main__":  # pragma: no cover - manual execution tool
    sys.exit(main())
