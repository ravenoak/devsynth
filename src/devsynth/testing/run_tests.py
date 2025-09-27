"""Shared pytest runner for DevSynth scripts and utilities.

This module provides a :func:`run_tests` function that executes pytest with
options compatible with DevSynth's CLI test commands. It is intended to be
intended for use by helper scripts such as ``scripts/manual_cli_testing.py``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import MutableMapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from devsynth.logging_setup import DevSynthLogger

# Cache directory for test collection
COLLECTION_CACHE_DIR = Path(".test_collection_cache")
TEST_COLLECTION_CACHE_FILE = COLLECTION_CACHE_DIR / "collection_cache.json"
# Standardized coverage outputs
COVERAGE_TARGET = "src/devsynth"
COVERAGE_JSON_PATH = Path("test_reports/coverage.json")
COVERAGE_HTML_DIR = Path("htmlcov")
LEGACY_HTML_DIRS: tuple[Path, ...] = (Path("test_reports/htmlcov"),)
DEFAULT_COVERAGE_THRESHOLD = (
    70.0  # Alpha release target; will increase to 90% for stable release
)
# TTL for collection cache in seconds (default: 3600); configurable via env var
try:
    COLLECTION_CACHE_TTL_SECONDS: int = int(
        os.environ.get("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "3600")
    )
except ValueError:
    # Fallback to default if malformed
    COLLECTION_CACHE_TTL_SECONDS = 3600


def _failure_tips(returncode: int, cmd: Sequence[str]) -> str:
    """Return actionable tips for troubleshooting pytest failures.

    Args:
        returncode: Exit code emitted by the ``pytest`` invocation.
        cmd: Command executed to run tests.

    Returns:
        A newline-prefixed string containing suggested next steps.
    """
    joined = " ".join(cmd)
    tips = [
        f"Pytest exited with code {returncode}. Command: {joined}",
        "Troubleshooting tips:",
        "- Smoke mode: reduce third-party plugin surface to isolate issues:",
        (
            "  poetry run devsynth run-tests --smoke --speed=fast --no-parallel "
            "--maxfail=1"
        ),
        "- Marker discipline: default is '-m not memory_intensive'.",
        "  Ensure exactly ONE of @pytest.mark.fast|medium|slow per test.",
        (
            "- Plugin autoload: avoid PYTEST_DISABLE_PLUGIN_AUTOLOAD unless using "
            "--smoke; plugin options may fail otherwise."
        ),
        (
            "- Diagnostics: run 'poetry run devsynth doctor' for a quick "
            "environment check."
        ),
        "- Narrow scope: use '-k <expr>' and '-vv' to focus a failure.",
        "- Segment large suites to localize failures and flakes:",
        (
            "  devsynth run-tests --target unit-tests --speed=fast --segment "
            "--segment-size=50"
        ),
        "- Limit failures early to speed iteration:",
        "  poetry run devsynth run-tests --target unit-tests --speed=fast --maxfail=1",
        "- Disable parallelism if xdist interaction is suspected:",
        "  devsynth run-tests --target unit-tests --speed=fast --no-parallel",
        ("- Generate an HTML report for context (saved under test_reports/):"),
        "  devsynth run-tests --target unit-tests --speed=fast --report",
    ]
    return "\n" + "\n".join(tips) + "\n"


# Mapping of CLI targets to test paths
TARGET_PATHS: dict[str, str] = {
    "unit-tests": "tests/unit/",
    "integration-tests": "tests/integration/",
    "behavior-tests": "tests/behavior/",
    "all-tests": "tests/",
}

logger = DevSynthLogger(__name__)


def _reset_coverage_artifacts() -> None:
    """Remove stale coverage artifacts before starting a test run."""

    COVERAGE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    for path in (
        Path(".coverage"),
        COVERAGE_JSON_PATH,
        Path("coverage.json"),
    ):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            # Never fail test execution due to cleanup issues
            logger.debug("Unable to remove coverage artifact: %s", path)
    for fragment in Path.cwd().glob(".coverage.*"):
        try:
            if fragment.is_file():
                fragment.unlink()
        except OSError:
            logger.debug("Unable to remove coverage fragment: %s", fragment)
    for directory in {COVERAGE_HTML_DIR, *LEGACY_HTML_DIRS}:
        try:
            if directory.exists():
                shutil.rmtree(directory)
        except OSError:
            logger.debug("Unable to remove coverage directory: %s", directory)


def _ensure_coverage_artifacts() -> None:
    """Generate coverage artifacts when real coverage data exists."""

    try:
        from coverage import Coverage
    except Exception:
        logger.debug("coverage library unavailable; skipping artifact generation")
        return

    data_path = Path(".coverage")
    fragments = sorted(Path.cwd().glob(".coverage.*"))
    if not data_path.exists() and fragments:
        try:
            coverage_for_combine = Coverage(data_file=str(data_path))
            coverage_for_combine.combine([str(path) for path in fragments])
            coverage_for_combine.save()
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning(
                "Unable to consolidate coverage fragments",
                extra={
                    "error": str(exc),
                    "fragments": [str(path) for path in fragments],
                    "coverage_data_file": str(data_path),
                },
            )
        else:
            logger.info(
                "Consolidated %d coverage fragments into %s",
                len(fragments),
                data_path,
                extra={
                    "coverage_data_file": str(data_path),
                    "fragment_count": len(fragments),
                },
            )
            for fragment in fragments:
                try:
                    fragment.unlink()
                except OSError as cleanup_error:  # pragma: no cover - defensive guard
                    logger.debug(
                        "Unable to remove coverage fragment",
                        extra={
                            "error": str(cleanup_error),
                            "fragment": str(fragment),
                        },
                    )

    if not data_path.exists():
        logger.warning(
            "Coverage artifact generation skipped: data file missing",
            extra={"coverage_data_file": str(data_path)},
        )
        return

    try:
        file_size = data_path.stat().st_size
    except OSError:  # pragma: no cover - defensive guard
        file_size = 0
    logger.info(
        "Coverage data file detected at %s (%d bytes)",
        data_path,
        file_size,
        extra={"coverage_data_file": str(data_path), "coverage_file_size": file_size},
    )

    try:
        cov = Coverage(data_file=str(data_path))
        cov.load()
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Coverage artifact generation skipped: unable to load data",
            extra={"error": str(exc), "coverage_data_file": str(data_path)},
        )
        return

    try:
        measured_files = list(cov.get_data().measured_files())
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Coverage artifact generation skipped: coverage data unreadable",
            extra={"error": str(exc)},
        )
        return

    if not measured_files:
        logger.warning(
            "Coverage artifact generation skipped: no measured files present",
            extra={"coverage_data_file": str(data_path)},
        )
        return

    COVERAGE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_HTML_DIR.mkdir(parents=True, exist_ok=True)
    for legacy_dir in LEGACY_HTML_DIRS:
        legacy_dir.parent.mkdir(parents=True, exist_ok=True)

    try:
        cov.html_report(directory=str(COVERAGE_HTML_DIR))
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Failed to write coverage HTML report",
            extra={"error": str(exc), "output_dir": str(COVERAGE_HTML_DIR)},
        )
    else:
        html_index = COVERAGE_HTML_DIR / "index.html"
        logger.info(
            "Coverage HTML report generated",
            extra={
                "coverage_html_index": str(html_index),
                "coverage_html_exists": html_index.exists(),
            },
        )
        for legacy_dir in LEGACY_HTML_DIRS:
            try:
                if legacy_dir.exists():
                    shutil.rmtree(legacy_dir)
                shutil.copytree(COVERAGE_HTML_DIR, legacy_dir, dirs_exist_ok=True)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.debug(
                    "Unable to synchronize legacy coverage directory",
                    extra={"error": str(exc), "legacy_dir": str(legacy_dir)},
                )

    try:
        cov.json_report(outfile=str(COVERAGE_JSON_PATH))
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Failed to write coverage JSON report",
            extra={"error": str(exc), "output_file": str(COVERAGE_JSON_PATH)},
        )
    else:
        logger.info(
            "Coverage JSON report generated",
            extra={"coverage_json_path": str(COVERAGE_JSON_PATH)},
        )
        try:
            shutil.copyfile(COVERAGE_JSON_PATH, Path("coverage.json"))
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.debug(
                "Unable to copy coverage JSON to legacy location",
                extra={"error": str(exc)},
            )


def _parse_pytest_addopts(addopts: str | None) -> list[str]:
    """Parse a ``PYTEST_ADDOPTS`` string into discrete tokens."""

    if not addopts or not addopts.strip():
        return []
    try:
        return shlex.split(addopts)
    except ValueError:
        # Fall back to a naive split when quoting is imbalanced; pytest will
        # still receive the original string and surface the parsing error.
        return addopts.split()


def _addopts_has_plugin(tokens: list[str], plugin: str) -> bool:
    """Return ``True`` when ``-p`` selects the given plugin."""

    for index, token in enumerate(tokens):
        if token == "-p" and index + 1 < len(tokens) and tokens[index + 1] == plugin:
            return True
        if token.startswith("-p") and token[2:] == plugin:
            return True
    return False


def _coverage_plugin_disabled(tokens: list[str]) -> bool:
    """Determine whether coverage instrumentation is explicitly disabled."""

    if "--no-cov" in tokens:
        return True
    if _addopts_has_plugin(tokens, "no:cov"):
        return True
    if _addopts_has_plugin(tokens, "no:pytest_cov"):
        return True
    return False


def _plugin_explicitly_disabled(tokens: list[str], plugin: str) -> bool:
    """Return ``True`` when ``-p no:<plugin>`` disables the given plugin."""

    return _addopts_has_plugin(tokens, f"no:{plugin}")


def ensure_pytest_cov_plugin_env(env: MutableMapping[str, str]) -> bool:
    """Ensure pytest-cov loads when plugin autoloading is disabled."""

    if env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
        return False

    addopts_value = env.get("PYTEST_ADDOPTS", "")
    tokens = _parse_pytest_addopts(addopts_value)

    if _coverage_plugin_disabled(tokens):
        logger.debug(
            "pytest-cov remains disabled due to explicit --no-cov or -p overrides",
            extra={"pytest_addopts": addopts_value},
        )
        return False

    if _addopts_has_plugin(tokens, "pytest_cov"):
        return False

    normalized = addopts_value.strip()
    updated = f"{normalized} -p pytest_cov".strip()
    env["PYTEST_ADDOPTS"] = updated
    logger.info(
        "Injected -p pytest_cov into PYTEST_ADDOPTS to preserve coverage instrumentation",
        extra={"pytest_addopts": updated},
    )
    return True

def ensure_pytest_bdd_plugin_env(env: MutableMapping[str, str]) -> bool:
    """Ensure pytest-bdd loads when plugin autoloading is disabled."""

    if env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
        return False

    addopts_value = env.get("PYTEST_ADDOPTS", "")
    tokens = _parse_pytest_addopts(addopts_value)

    plugin_aliases = ("pytest_bdd", "pytest_bdd.plugin")
    if any(_plugin_explicitly_disabled(tokens, alias) for alias in plugin_aliases):
        logger.debug(
            "pytest-bdd remains disabled due to explicit -p no:pytest_bdd override",
            extra={"pytest_addopts": addopts_value},
        )
        return False

    if _addopts_has_plugin(tokens, "pytest_bdd.plugin"):
        return False

    normalized = addopts_value.strip()
    updated = f"{normalized} -p pytest_bdd.plugin".strip()
    env["PYTEST_ADDOPTS"] = updated
    logger.info(
        "Injected -p pytest_bdd.plugin into PYTEST_ADDOPTS to preserve pytest-bdd hooks",
        extra={"pytest_addopts": updated},
    )
    return True

def coverage_artifacts_status() -> tuple[bool, str | None]:
    """Return whether generated coverage artifacts contain useful data."""

    if not COVERAGE_JSON_PATH.exists():
        return False, f"Coverage JSON missing at {COVERAGE_JSON_PATH}"

    try:
        payload = json.loads(COVERAGE_JSON_PATH.read_text())
    except json.JSONDecodeError as exc:
        return False, f"Coverage JSON invalid: {exc}"

    totals = payload.get("totals") if isinstance(payload, dict) else None
    if not isinstance(totals, dict) or "percent_covered" not in totals:
        return False, "Coverage JSON missing totals.percent_covered"

    html_index = COVERAGE_HTML_DIR / "index.html"
    if not html_index.exists():
        return False, f"Coverage HTML missing at {html_index}"

    try:
        html_body = html_index.read_text()
    except OSError as exc:  # pragma: no cover - defensive guard
        return False, f"Coverage HTML unreadable: {exc}"

    if "No coverage data available" in html_body:
        return False, "Coverage HTML indicates no recorded data"

    return True, None

def enforce_coverage_threshold(
    coverage_file: Path | str = COVERAGE_JSON_PATH,
    minimum_percent: float = DEFAULT_COVERAGE_THRESHOLD,
    *,
    exit_on_failure: bool = True,
) -> float:
    """Ensure the aggregated coverage percentage meets the required minimum."""

    path = Path(coverage_file)
    try:
        raw = path.read_text()
    except FileNotFoundError:
        message = f"Coverage report not found at {path}."
        logger.error(message)
        if exit_on_failure:
            raise SystemExit(1)
        raise RuntimeError(message)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        message = f"Coverage JSON at {path} is invalid: {exc}"
        logger.error(message)
        if exit_on_failure:
            raise SystemExit(1)
        raise RuntimeError(message) from exc

    totals = payload.get("totals") if isinstance(payload, dict) else None
    percent_value: float | None = None
    if isinstance(totals, dict):
        raw_percent = totals.get("percent_covered")
        if isinstance(raw_percent, (int, float)):
            percent_value = float(raw_percent)

    if percent_value is None:
        message = (
            f"Unable to determine total coverage from {path}; 'totals.percent_covered'"
            " missing."
        )
        logger.error(message)
        if exit_on_failure:
            raise SystemExit(1)
        raise RuntimeError(message)

    if percent_value < minimum_percent:
        message = f"Coverage {percent_value:.2f}% is below the required {minimum_percent:.2f}%"
        logger.error(message)
        if exit_on_failure:
            raise SystemExit(1)
        raise RuntimeError(message)

    logger.info(
        "Coverage %.2f%% meets the %.2f%% threshold.", percent_value, minimum_percent
    )
    return percent_value


def _sanitize_node_ids(ids: list[str]) -> list[str]:
    """Normalize and deduplicate pytest selection IDs.

    Args:
        ids: Raw node identifiers collected from ``pytest --collect-only``.

    Returns:
        A list of unique node identifiers with redundant line-number suffixes
        removed.
    """
    seen = set()
    out: list[str] = []
    for nid in ids:
        cleaned = nid
        # Only strip a trailing line number if there is no function/class delimiter.
        if "::" not in cleaned:
            cleaned = re.sub(r":\d+$", "", cleaned)
        if cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def collect_tests_with_cache(
    target: str, speed_category: str | None = None
) -> list[str]:
    print(
        f"collect_tests_with_cache called for target: {target}, speed_category: {speed_category}"
    )  # Debug print
    """Collect tests for the given target and speed category."""
    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])

    # Build the marker expression we'll use and compute a simple fingerprint of
    # the test tree (latest mtime) to detect changes that should invalidate cache.
    marker_expr = "not memory_intensive"
    category_expr = marker_expr
    if speed_category:
        category_expr = f"{speed_category} and {marker_expr}"

    def _latest_mtime(root: str) -> float:
        latest = 0.0
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".py"):
                    try:
                        mtime = os.path.getmtime(os.path.join(dirpath, fn))
                        if mtime > latest:
                            latest = mtime
                    except OSError:
                        # Ignore transient filesystem errors
                        continue
        return latest

    latest_mtime = _latest_mtime(test_path)
    cache_key = f"{target}_{speed_category or 'all'}"
    cache_file = (
        COLLECTION_CACHE_DIR / f"{cache_key}_tests.json"
    )  # Use Path object for cache_file

    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cached_data: dict[str, Any] = json.load(f)

            stored_timestamp_str = cached_data.get("timestamp")
            stored_mtime = cached_data.get("fingerprint", {}).get("latest_mtime")
            stored_category_expr = cached_data.get("fingerprint", {}).get(
                "category_expr"
            )
            stored_test_path = cached_data.get("fingerprint", {}).get("test_path")

            cache_time = (
                datetime.fromisoformat(stored_timestamp_str)
                if stored_timestamp_str
                else None
            )

            # Correct comparison of fingerprint elements
            fingerprint_matches = (
                (stored_mtime == latest_mtime)
                and (stored_category_expr == category_expr)
                and (stored_test_path == test_path)
            )

            if (
                cache_time
                and (datetime.now() - cache_time).total_seconds()
                < COLLECTION_CACHE_TTL_SECONDS
                and fingerprint_matches
            ):
                logger.info(
                    (
                        "Using cached test collection for %s (%s) [TTL=%ss; "
                        "fingerprint ok]"
                    ),
                    target,
                    speed_category or "all",
                    COLLECTION_CACHE_TTL_SECONDS,
                )
                return cast(list[str], cached_data["tests"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("Error loading test collection cache: %s", e)
            # Fall through to regenerate
            pass

    COLLECTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)  # Use Path method

    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "--collect-only",
        "-q",
        "-o",
        "addopts=",
        "-m",
        category_expr,
    ]

    try:
        result = subprocess.run(
            collect_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout for collection
        )
        if result.returncode != 0:
            error_message = f"Test collection failed: {result.stderr}"
            logger.warning(error_message)
            raise RuntimeError(error_message)

        # Parse node IDs from output
        node_ids = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and "::" in line and not line.startswith("="):
                node_ids.append(line)

        # Cache the results
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tests": node_ids,
            "fingerprint": {
                "latest_mtime": latest_mtime,
                "category_expr": category_expr,
                "test_path": test_path,
            },
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        logger.debug(
            "Collected %d tests for %s (%s) [cached for %ss]",
            len(node_ids),
            target,
            speed_category or "all",
            COLLECTION_CACHE_TTL_SECONDS,
        )
        return node_ids

    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("Test collection failed: %s", e)
        return []


def run_tests(
    target: str,
    speed_categories: list[str] | None = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int | None = None,
    maxfail: int | None = None,
    extra_marker: str | None = None,
    keyword_filter: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Run tests using pytest with DevSynth-compatible options.

    Args:
        target: Test target (e.g., 'unit-tests', 'integration-tests', 'all-tests')
        speed_categories: List of speed markers to include (e.g., ['fast', 'medium'])
        verbose: Enable verbose output
        report: Generate HTML coverage report
        parallel: Enable parallel execution with pytest-xdist
        segment: Enable segmented execution for large test suites
        segment_size: Number of tests per segment when segmenting
        maxfail: Stop after N failures
        extra_marker: Additional marker expression
        keyword_filter: Keyword filter for test selection
        env: Environment variables to pass to subprocess

    Returns:
        Tuple of (success: bool, output: str)
    """
    if env is None:
        env = os.environ.copy()

    # Reset coverage artifacts
    _reset_coverage_artifacts()

    # Ensure coverage plugins are available
    ensure_pytest_cov_plugin_env(env)
    ensure_pytest_bdd_plugin_env(env)

    # Build marker expression
    marker_parts = ["not memory_intensive"]
    if speed_categories:
        speed_expr = " or ".join(speed_categories)
        marker_parts.append(f"({speed_expr})")
    if extra_marker:
        marker_parts.append(f"({extra_marker})")

    marker_expr = " and ".join(marker_parts)

    # Validate target
    if target not in TARGET_PATHS:
        raise ValueError(
            f"Unknown test target: '{target}'. "
            f"Available targets are: {', '.join(TARGET_PATHS.keys())}"
        )

    # Collect tests
    try:
        collected_node_ids = collect_tests_with_cache(
            target, speed_categories[0] if speed_categories else None
        )
    except RuntimeError as e:
        return False, str(e)

    marker_fallback = False
    if not collected_node_ids:
        logger.info(
            "marker fallback triggered for target=%s (speeds=%s)",
            target,
            ",".join(speed_categories or ["all"]),
        )
        marker_fallback = True
        collected_node_ids = [TARGET_PATHS[target]]

    if segment and speed_categories and not marker_fallback:
        # Segmented execution
        return _run_segmented_tests(
            target=target,
            speed_categories=speed_categories,
            marker_expr=marker_expr,
            node_ids=collected_node_ids,  # Pass collected node_ids
            verbose=verbose,
            report=report,
            parallel=parallel,
            segment_size=segment_size or 50,
            maxfail=maxfail,
            keyword_filter=keyword_filter,
            env=env,
        )

    # Single execution
    success, output = _run_single_test_batch(
        node_ids=collected_node_ids,  # Pass collected node_ids
        marker_expr=marker_expr,
        verbose=verbose,
        report=report,
        parallel=parallel,
        maxfail=maxfail,
        keyword_filter=keyword_filter,
        env=env,
    )
    _ensure_coverage_artifacts()
    if marker_fallback:
        output = "Marker fallback executed.\n" + output
    return success, output


def _run_segmented_tests(
    target: str,
    speed_categories: list[str],
    marker_expr: str,
    node_ids: list[str],  # Changed from test_path: str
    verbose: bool,
    report: bool,
    parallel: bool,
    segment_size: int,
    maxfail: int | None,
    keyword_filter: str | None,
    env: dict[str, str],
) -> tuple[bool, str]:
    """Run tests in segments to handle large test suites."""
    all_outputs = []
    overall_success = True

    # Sanitize node IDs
    node_ids = _sanitize_node_ids(node_ids)

    # Split into segments
    segments = [
        node_ids[i : i + segment_size] for i in range(0, len(node_ids), segment_size)
    ]

    logger.info(
        "Running %d tests in %d segments of size %d for target=%s",
        len(node_ids),
        len(segments),
        segment_size,
        target,
    )

    for i, segment_nodes in enumerate(segments):
        if not segment_nodes:
            continue

        logger.info(
            "Running segment %d/%d (%d tests)", i + 1, len(segments), len(segment_nodes)
        )

        success, output = _run_single_test_batch(
            node_ids=segment_nodes,  # Pass collected node_ids
            marker_expr=marker_expr,
            verbose=verbose,
            report=
            report
            and (i == len(segments) - 1),  # Only generate report on last segment
            parallel=parallel,
            maxfail=maxfail,
            keyword_filter=keyword_filter,
            env=env,
        )

        all_outputs.append(output)
        if not success:
            overall_success = False
            if maxfail:
                break  # Stop on first failure if maxfail is set

    # Ensure coverage artifacts are generated
    _ensure_coverage_artifacts()

    return overall_success, "\n".join(all_outputs)


def _run_single_test_batch(
    node_ids: list[str],  # Changed from test_path: str
    marker_expr: str,
    verbose: bool,
    report: bool,
    parallel: bool,
    maxfail: int | None,
    keyword_filter: str | None,
    env: dict[str, str],
) -> tuple[bool, str]:
    """Run a single batch of tests."""
    cmd = [sys.executable, "-m", "pytest"]

    # Add test node IDs
    cmd.extend(node_ids)

    # Add marker expression
    cmd.extend(["-m", marker_expr])

    # Add coverage options
    cmd.extend(
        [
            f"--cov={COVERAGE_TARGET}",
            f"--cov-report=json:{COVERAGE_JSON_PATH}",
            f"--cov-report=html:{COVERAGE_HTML_DIR}",
            "--cov-append",
        ]
    )

    # Add other options
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    if maxfail:
        cmd.extend(["--maxfail", str(maxfail)])
    if keyword_filter:
        cmd.extend(["-k", keyword_filter])
    if report:
        # HTML report is already handled by coverage
        pass

    # Disable plugin autoload in smoke mode
    if env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1":
        # Explicitly enable required plugins
        addopts = env.get("PYTEST_ADDOPTS", "")
        if "-p pytest_cov" not in addopts:
            env["PYTEST_ADDOPTS"] = f"{addopts} -p pytest_cov -p pytest_bdd".strip()

    try:
        logger.debug("Running command: %s", " ".join(cmd))
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        output, _ = process.communicate()
        success = process.returncode in (0, 5)  # 0 = success, 5 = no tests collected

        if not success:
            output += _failure_tips(process.returncode, cmd)

        return success, output
    except Exception as e:
        error_msg = f"Failed to run tests: {e}"
        logger.error(error_msg)
        return False, error_msg

if __name__ == "__main__":
    # This block is for internal testing and coverage analysis.
    # It is not meant to be run as part of the normal test suite.
    print("Running internal tests for run_tests.py...")
    temp_dir = Path("./temp_test_run_tests")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    os.chdir(temp_dir)

    # Test: _reset_coverage_artifacts handles OSError
    print("  Testing _reset_coverage_artifacts OSError handling...")
    unwritable_dir = Path("unwritable_reset")
    unwritable_dir.mkdir()
    (unwritable_dir / ".coverage").touch()
    os.chmod(unwritable_dir, 0o555)
    # We need to mock the paths to point into our unwritable dir
    with patch("devsynth.testing.run_tests.Path") as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_file.return_value = True
        mock_path.return_value.glob.return_value = [unwritable_dir / ".coverage"]
        _reset_coverage_artifacts()
    os.chmod(unwritable_dir, 0o755)
    print("  ...done.")

    # Cleanup for next test
    shutil.rmtree(unwritable_dir)

    # Test: enforce_coverage_threshold
    print("  Testing enforce_coverage_threshold...")
    coverage_file = Path("coverage.json")

    # Test success
    coverage_file.write_text(json.dumps({"totals": {"percent_covered": 95.0}}))
    enforce_coverage_threshold(coverage_file, minimum_percent=90.0, exit_on_failure=False)
    print("    - Success case passed.")

    # Test failure
    coverage_file.write_text(json.dumps({"totals": {"percent_covered": 75.0}}))
    try:
        enforce_coverage_threshold(coverage_file, minimum_percent=80.0, exit_on_failure=False)
    except RuntimeError as e:
        assert "below the required" in str(e)
        print("    - Failure case passed.")

    # Test missing file
    coverage_file.unlink()
    try:
        enforce_coverage_threshold(coverage_file, exit_on_failure=False)
    except RuntimeError as e:
        assert "not found" in str(e)
        print("    - Missing file case passed.")

    # Test invalid JSON
    coverage_file.write_text("invalid json")
    try:
        enforce_coverage_threshold(coverage_file, exit_on_failure=False)
    except RuntimeError as e:
        assert "is invalid" in str(e)
        print("    - Invalid JSON case passed.")

    # Test missing key
    coverage_file.write_text(json.dumps({"totals": {}}))
    try:
        enforce_coverage_threshold(coverage_file, exit_on_failure=False)
    except RuntimeError as e:
        assert "missing" in str(e)
        print("    - Missing key case passed.")

    coverage_file.unlink()
    print("  ...done.")

    print("Internal tests finished.")
    # Go back to original directory
    os.chdir("..")
    shutil.rmtree(temp_dir)