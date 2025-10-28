#!/usr/bin/env python3
"""
Fix missing speed markers in test functions by adding @pytest.mark.medium conservatively.

Usage:
  python scripts/fix_missing_markers.py [--path PATH] [--dry-run] [--verbose]

Behavior:
- Scans test files under tests/ (or a provided PATH) for test functions without any
  of the allowed speed markers: @pytest.mark.fast, @pytest.mark.medium, @pytest.mark.slow.
- Adds @pytest.mark.medium directly above such test functions.
- Preserves other non-speed markers and existing valid speed markers.
- Skips files that are already fully compliant.

Notes:
- This script relies on scripts/common_test_collector.py for consistent marker detection
  (check_test_has_marker and collect_tests) to mirror the repo's verifier.
- Designed to be idempotent.

Exit codes:
- 0: success (or no changes when --dry-run)
- 1: unexpected error
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure we can import sibling helper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        check_test_has_marker,
        collect_tests,
        invalidate_cache_for_files,
    )
except Exception:  # pragma: no cover - fallback if collector not importable
    check_test_has_marker = None  # type: ignore
    collect_tests = None  # type: ignore
    invalidate_cache_for_files = None  # type: ignore

SPEED_MARKERS = ["fast", "medium", "slow"]
MARKER_PATTERN = re.compile(r"^\s*@pytest\.mark\.(fast|medium|slow)\b")
FUNC_DEF_PATTERN = re.compile(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(")
CLASS_DEF_PATTERN = re.compile(r"^\s*class\s+([A-Za-z0-9_]+)\s*\(")
PYTEST_MARK_IMPORT = re.compile(r"^\s*import\s+pytest\b|^\s*from\s+pytest\s+import\b")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fix missing speed markers in tests")
    p.add_argument(
        "--path", default="tests", help="Directory or file to process (default: tests)"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing files"
    )
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    return p.parse_args()


def _ensure_pytest_import(lines: list[str]) -> tuple[list[str], bool]:
    # Ensure pytest is imported; if not, add `import pytest` after module docstring or shebang
    has_import = any(PYTEST_MARK_IMPORT.search(l) for l in lines)
    if has_import:
        return lines, False
    insert_idx = 0
    if lines and lines[0].startswith("#!/"):
        insert_idx = 1
    # Skip module docstring block if present
    if insert_idx < len(lines) and lines[insert_idx].lstrip().startswith(
        ('"""', "'''")
    ):
        quote = lines[insert_idx].lstrip()[:3]
        insert_idx += 1
        while insert_idx < len(lines):
            if lines[insert_idx].lstrip().startswith(quote):
                insert_idx += 1
                break
            insert_idx += 1
    new_lines = lines[:insert_idx] + ["import pytest\n"] + lines[insert_idx:]
    return new_lines, True


def _insert_marker_above(lines: list[str], idx: int) -> None:
    # Insert @pytest.mark.medium above function def, respecting indentation
    indent = len(lines[idx]) - len(lines[idx].lstrip(" "))
    lines.insert(idx, " " * indent + "@pytest.mark.medium\n")


def _file_has_module_level_speed_marker(lines: list[str]) -> bool:
    # We do not add/alter module-level speed markers; verifier will flag them elsewhere.
    # Here, we just detect them to avoid false positives when counting missing markers.
    for line in lines:
        if MARKER_PATTERN.match(line) and "def " + "test_" not in line:
            return True
    return False


def process_file(
    path: Path, dry_run: bool = False, verbose: bool = False
) -> tuple[bool, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Optionally use collector to find tests and whether they already have markers
    test_functions: list[tuple[int, str]] = []  # (line_index, func_name)

    # Simple parse: track class context for class-based tests; still fine for decorator insertion
    class_stack: list[str] = []
    for i, line in enumerate(lines):
        class_m = CLASS_DEF_PATTERN.match(line)
        if class_m:
            # Track class
            class_stack.append(class_m.group(1))
            continue
        if line.strip().startswith("class ") and not CLASS_DEF_PATTERN.match(line):
            # reset if unusual class syntax we don't handle
            class_stack = []
        m = FUNC_DEF_PATTERN.match(line)
        if m:
            name = m.group(1)
            if name.startswith("test_"):
                test_functions.append((i, name))

    if not test_functions:
        return False, 0

    # Determine which need markers
    inserts: list[int] = []
    for idx, name in test_functions:
        # Walk upwards skipping blank lines and comments to see if a speed marker already exists immediately above
        j = idx - 1
        has_speed_marker = False
        while j >= 0 and (lines[j].strip() == "" or lines[j].lstrip().startswith("@")):
            if MARKER_PATTERN.match(lines[j]):
                has_speed_marker = True
                break
            j -= 1
        if not has_speed_marker:
            # Optionally consult collector if available for more robust detection (e.g., parametrize markers)
            marked = False
            if check_test_has_marker is not None:
                try:
                    # Build relative path for collector
                    rel = str(path)
                    # The collector expects a test identifier path; approximate with file::func
                    # If it can't find, fall back to local check
                    marked = check_test_has_marker(rel + "::" + name, SPEED_MARKERS, record_timestamp=False)  # type: ignore
                except Exception:
                    marked = False
            if not marked:
                inserts.append(idx)

    if not inserts:
        return False, 0

    # Ensure pytest import exists if we will add decorators
    lines, added_import = _ensure_pytest_import(lines)
    import_added_offset = 1 if added_import else 0

    # Adjust indices if import inserted before some functions
    adjusted_inserts = []
    for idx in inserts:
        if added_import:
            # If import inserted before this index, shift by 1
            adjusted_inserts.append(idx + import_added_offset if idx >= 0 else idx)
        else:
            adjusted_inserts.append(idx)

    # Perform insertions from bottom to top to keep indices valid
    for idx in sorted(adjusted_inserts, reverse=True):
        _insert_marker_above(lines, idx)

    if dry_run:
        if verbose:
            print(
                f"[DRY] Would modify {path} adding {len(adjusted_inserts)} @pytest.mark.medium decorators"
            )
        return False, len(adjusted_inserts)

    path.write_text("".join(lines), encoding="utf-8")

    # Invalidate caches for verifier
    if invalidate_cache_for_files is not None:
        try:
            invalidate_cache_for_files([str(path)], verbose=verbose)  # type: ignore
        except Exception:
            pass

    if verbose:
        print(
            f"Updated {path}: added {len(adjusted_inserts)} @pytest.mark.medium decorators"
        )
    return True, len(adjusted_inserts)


def discover_targets(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    paths: list[Path] = []
    for p in root.rglob("test_*.py"):
        if "/.venv/" in str(p) or "__pycache__" in str(p.parts):
            continue
        paths.append(p)
    return paths


def main() -> int:
    args = parse_args()
    target = Path(args.path)
    files = discover_targets(target)
    if args.verbose:
        print(f"Scanning {len(files)} files under {target}")
    total_added = 0
    modified_files: list[str] = []

    for f in files:
        try:
            changed, added = process_file(f, dry_run=args.dry_run, verbose=args.verbose)
        except Exception as e:  # robust loop
            print(f"Error processing {f}: {e}", file=sys.stderr)
            continue
        total_added += added
        if changed:
            modified_files.append(str(f))

    if args.verbose:
        print(f"Added {total_added} decorators across {len(modified_files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
