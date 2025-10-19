#!/usr/bin/env python3
"""
Fast+Medium coverage orchestration and archival helper.

This script performs the following steps to satisfy the release evidence flow:

1) Ensure diagnostics folder exists and compute UTC timestamp.
2) Execute the aggregate fast+medium coverage profile:
   poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel --maxfail=1
   The full CLI transcript is tee'd to diagnostics/devsynth_run_tests_fast_medium_<UTC>.log.
3) Verify exit code 0 and that the CLI printed the QualityGate banner.
4) Confirm regenerated artifacts show ≥90% using test_reports/coverage.json totals.percent_covered.
   Also try to locate test_reports/coverage_manifest_<UTC>.json (or fall back to coverage_manifest_latest.json).
5) Archive evidence under artifacts/releases/<release_tag>/fast-medium/<UTC>-fast-medium/ including:
   - The CLI transcript from step 2.
   - The JSON manifest(s) and coverage.json (and coverage.xml if present).
   - A zipped HTML report with SHA-256 noted in a short archive_manifest.json.

Notes
- This script does not modify core logic; it is a workflow convenience wrapper.
- It prefers repository-native helpers (e.g., release tag detection) when available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_REPORTS = REPO_ROOT / "test_reports"
DIAGNOSTICS = REPO_ROOT / "diagnostics"
HTMLCOV = REPO_ROOT / "htmlcov"
COVERAGE_JSON = TEST_REPORTS / "coverage.json"
COVERAGE_XML = REPO_ROOT / "coverage.xml"


def _utc_ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _get_release_tag() -> str:
    try:
        from devsynth.release.publish import get_release_tag  # type: ignore

        return get_release_tag()
    except Exception:
        # Fallback to pyproject if available
        try:
            import tomllib  # py312+

            payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
            version = payload.get("tool", {}).get("poetry", {}).get("version")
            if isinstance(version, str):
                return version
        except Exception:
            pass
        return "unknown"


def _run_and_tee(cmd: list[str], log_path: Path) -> tuple[int, str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    output_lines: list[str] = []
    with log_path.open("w", encoding="utf-8") as log:
        assert proc.stdout is not None
        for line in proc.stdout:
            output_lines.append(line)
            log.write(line)
            # also echo to console live
            sys.stdout.write(line)
    returncode = proc.wait()
    return returncode, "".join(output_lines)


def _find_manifest(ts: str) -> tuple[Optional[Path], Path]:
    exact = TEST_REPORTS / f"coverage_manifest_{ts}.json"
    latest = TEST_REPORTS / "coverage_manifest_latest.json"
    return (exact if exact.exists() else None), latest


def _verify_coverage_threshold(minimum: float) -> float:
    if not COVERAGE_JSON.exists():
        raise RuntimeError(f"Coverage JSON missing at {COVERAGE_JSON}")
    payload = _read_json(COVERAGE_JSON)
    totals = payload.get("totals") if isinstance(payload, dict) else None
    if not isinstance(totals, dict) or "percent_covered" not in totals:
        raise RuntimeError("Coverage JSON missing totals.percent_covered")
    percent = float(totals["percent_covered"])  # type: ignore[arg-type]
    if percent < minimum:
        raise RuntimeError(
            f"Coverage {percent:.2f}% is below the required {minimum:.2f}%"
        )
    return percent


def _zip_htmlcov(to_path: Path) -> str:
    to_path.parent.mkdir(parents=True, exist_ok=True)
    # Use tar.gz for portability in repo
    # Convert .zip request into .tar.gz while still computing checksum.
    with tarfile.open(to_path, "w:gz") as tar:
        tar.add(HTMLCOV, arcname="htmlcov")
    return _sha256(to_path)


def archive_fast_medium(cycle: Optional[str] = None, min_percent: float = 90.0) -> int:
    ts = _utc_ts()
    # Step 1: run tests and tee log
    log_path = DIAGNOSTICS / f"devsynth_run_tests_fast_medium_{ts}.log"
    cmd = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--speed=fast",
        "--speed=medium",
        "--report",
        "--no-parallel",
        "--maxfail=1",
    ]
    # Ensure provider subsystem stubs are not applied for unit tests that assert
    # against real provider classes/types.
    os.environ.setdefault("DEVSYNTH_TEST_ALLOW_PROVIDERS", "true")

    rc, output = _run_and_tee(cmd, log_path)
    if rc != 0:
        raise SystemExit(rc)

    # Step 2: check banner indicator
    banner_ok = "coverage gate" in output and "QualityGate" in output and "coverage=" in output
    if not banner_ok:
        # Not fatal per se, but per requirements we should stop and debug
        raise RuntimeError(
            "QualityGate banner not detected in CLI output; inspect diagnostics log."
        )

    # Step 3: verify coverage ≥ threshold
    percent = _verify_coverage_threshold(min_percent)

    # Step 4: locate manifests
    exact_manifest, latest_manifest = _find_manifest(ts)

    # Step 5: compose archive destination
    release_tag = cycle or _get_release_tag()
    profile = "fast-medium"
    dest_root = (
        REPO_ROOT
        / "artifacts"
        / "releases"
        / release_tag
        / profile
        / f"{ts}-{profile}"
    )
    dest_root.mkdir(parents=True, exist_ok=True)

    # Step 6: copy files
    shutil.copy2(log_path, dest_root / log_path.name)
    if exact_manifest is not None:
        shutil.copy2(exact_manifest, dest_root / exact_manifest.name)
    if latest_manifest.exists():
        shutil.copy2(latest_manifest, dest_root / latest_manifest.name)
    if COVERAGE_JSON.exists():
        shutil.copy2(COVERAGE_JSON, dest_root / "coverage.json")
    if COVERAGE_XML.exists():
        shutil.copy2(COVERAGE_XML, dest_root / "coverage.xml")

    # Step 7: archive HTML and compute checksum
    tar_name = f"htmlcov-{ts}-{profile}.tar.gz"
    tar_path = dest_root / tar_name
    html_sha256 = _zip_htmlcov(tar_path)

    # Step 8: write short manifest with checksums and summary
    archive_manifest = {
        "timestamp": ts,
        "release_tag": release_tag,
        "profile": profile,
        "coverage_percent": percent,
        "artifacts": [
            {"path": str((dest_root / log_path.name).relative_to(REPO_ROOT)), "type": "cli_log"},
            {"path": str((dest_root / "coverage.json").relative_to(REPO_ROOT)), "type": "coverage_json"},
            {"path": str((dest_root / "coverage.xml").relative_to(REPO_ROOT)), "type": "coverage_xml", "optional": True},
            {"path": str(tar_path.relative_to(REPO_ROOT)), "type": "coverage_html_targz", "sha256": html_sha256},
        ],
    }
    if exact_manifest is not None:
        archive_manifest["manifest_exact"] = str((dest_root / exact_manifest.name).relative_to(REPO_ROOT))
    if latest_manifest.exists():
        archive_manifest["manifest_latest"] = str((dest_root / latest_manifest.name).relative_to(REPO_ROOT))

    (dest_root / "archive_manifest.json").write_text(json.dumps(archive_manifest, indent=2))

    # Echo final status for operator
    print(
        f"Archived fast+medium coverage: {percent:.2f}% → {dest_root.relative_to(REPO_ROOT)}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive fast+medium coverage run")
    parser.add_argument(
        "--cycle",
        help="Release cycle/tag to archive under (defaults to detected project version)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90.0,
        help="Minimum required coverage percent (default: 90.0)",
    )
    args = parser.parse_args()
    try:
        return archive_fast_medium(cycle=args.cycle, min_percent=args.threshold)
    except SystemExit as exc:
        # propagate poetry/devsynth exit code
        return int(exc.code)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
