#!/usr/bin/env python3
"""CLI utility to enforce minimum coverage from test_reports/coverage.json."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from devsynth.testing.run_tests import COVERAGE_JSON_PATH as DEFAULT_RELATIVE_PATH
from devsynth.testing.run_tests import (
    DEFAULT_COVERAGE_THRESHOLD,
)

ROOT = Path(__file__).resolve().parents[1]

EXIT_SUCCESS = 0
EXIT_BELOW_THRESHOLD = 1
EXIT_MISSING_REPORT = 2
EXIT_INVALID_REPORT = 3


class CoverageError(Exception):
    """Base class for coverage verification errors."""

    exit_code: int = EXIT_INVALID_REPORT


class CoverageReportNotFoundError(CoverageError):
    """Raised when the coverage JSON file cannot be found."""

    exit_code = EXIT_MISSING_REPORT


class CoverageReportInvalidError(CoverageError):
    """Raised when the coverage JSON file cannot be parsed."""

    exit_code = EXIT_INVALID_REPORT


class CoverageBelowThresholdError(CoverageError):
    """Raised when coverage does not meet the required threshold."""

    exit_code = EXIT_BELOW_THRESHOLD


@dataclass
class CoverageCheckResult:
    """Structured result of a coverage verification."""

    percent_covered: float
    threshold: float
    source: Path


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def _load_percent(path: Path) -> float:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - handled in main
        raise CoverageReportNotFoundError(
            f"Coverage report not found at {path}"
        ) from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CoverageReportInvalidError(
            f"Coverage JSON at {path} is invalid: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise CoverageReportInvalidError(
            f"Coverage report at {path} is not a JSON object."
        )

    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise CoverageReportInvalidError(
            f"Coverage report at {path} is missing 'totals'."
        )

    percent = totals.get("percent_covered")
    if not isinstance(percent, (int, float)):
        raise CoverageReportInvalidError(
            f"Coverage report at {path} is missing 'totals.percent_covered'."
        )

    return float(percent)


def verify_coverage(coverage_file: Path, threshold: float) -> CoverageCheckResult:
    percent = _load_percent(coverage_file)
    if percent < threshold:
        raise CoverageBelowThresholdError(
            f"Coverage {percent:.2f}% is below the required {threshold:.2f}%"
        )
    return CoverageCheckResult(
        percent_covered=percent,
        threshold=threshold,
        source=coverage_file,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify test coverage meets the required threshold."
    )
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=DEFAULT_RELATIVE_PATH,
        help="Path to the pytest coverage JSON report.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_COVERAGE_THRESHOLD,
        help="Minimum acceptable total coverage percentage (default: %(default)s).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    coverage_path = _resolve_path(Path(args.coverage_file))
    threshold = float(args.threshold)

    try:
        result = verify_coverage(coverage_path, threshold)
    except CoverageError as exc:
        print(f"[coverage-threshold] {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        print(f"[coverage-threshold] Unexpected error: {exc}", file=sys.stderr)
        return EXIT_INVALID_REPORT

    print(
        "[coverage-threshold] Coverage %.2f%% meets the %.2f%% threshold (%s)"
        % (result.percent_covered, result.threshold, result.source)
    )
    return EXIT_SUCCESS


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
