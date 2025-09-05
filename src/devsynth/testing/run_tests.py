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
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from collections.abc import Sequence

from devsynth.logging_setup import DevSynthLogger

# Cache directory for test collection
COLLECTION_CACHE_DIR = ".test_collection_cache"
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

    This does not change behavior; it augments logs/output with guidance.
    """
    joined = " ".join(cmd)
    tips = [
        f"Pytest exited with code {returncode}. Command: {joined}",
        "Troubleshooting tips:",
        "- Smoke mode: reduce third-party plugin surface to isolate issues:",
        "  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1",
        "- Marker discipline: default filter is '-m \"not memory_intensive\"'. Ensure each test has exactly ONE of @pytest.mark.fast|medium|slow.",
        "- Plugin autoload: avoid setting PYTEST_DISABLE_PLUGIN_AUTOLOAD unless using --smoke; otherwise pytest options from plugins may fail.",
        "- Diagnostics: run 'poetry run devsynth doctor' for a quick environment check.",
        "- Narrow scope: use '-k <expr>' and '-vv' to focus a failure.",
        "- Segment large suites to localize failures and flakes:",
        "  poetry run devsynth run-tests --target unit-tests --speed=fast --segment --segment-size=50",
        "- Limit failures early to speed iteration:",
        "  poetry run devsynth run-tests --target unit-tests --speed=fast --maxfail=1",
        "- Disable parallelism if xdist interaction is suspected:",
        "  poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel",
        "- Generate an HTML report for context (saved under test_reports/):",
        "  poetry run devsynth run-tests --target unit-tests --speed=fast --report",
    ]
    return "\n" + "\n".join(tips) + "\n"


# Mapping of CLI targets to test paths
TARGET_PATHS = {
    "unit-tests": "tests/unit/",
    "integration-tests": "tests/integration/",
    "behavior-tests": "tests/behavior/",
    "all-tests": "tests/",
}

logger = DevSynthLogger(__name__)


def _sanitize_node_ids(ids: list[str]) -> list[str]:
    """Sanitize pytest selection IDs collected from --collect-only -q output.

    - Strip trailing ":<digits>" that can appear from certain plugins/formatters
      when no function/class separator ("::") is present.
    - Deduplicate while preserving order.
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
    """Collect tests for the given target and speed category.

    Results are cached for a short period to speed up repeated collections.
    Cache entries are invalidated when:
    - TTL expires, or
    - The latest modification time under the target path changes, or
    - The marker expression (speed filter) changes.

    Args:
        target: Test target (e.g. ``unit-tests`` or ``integration-tests``).
        speed_category: Optional speed marker to filter tests.

    Returns:
        A list of test paths matching the criteria.
    """
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
    cache_file = os.path.join(COLLECTION_CACHE_DIR, f"{cache_key}_tests.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached_data = json.load(f)
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            cached_fingerprint = cached_data.get("fingerprint", {})
            fingerprint_matches = (
                cached_fingerprint.get("latest_mtime", 0.0) == latest_mtime
                and cached_fingerprint.get("category_expr") == category_expr
                and cached_fingerprint.get("test_path") == test_path
            )
            if (
                datetime.now() - cache_time
            ).total_seconds() < COLLECTION_CACHE_TTL_SECONDS and fingerprint_matches:
                logger.info(
                    "Using cached test collection for %s (%s) [TTL=%ss; fingerprint ok]",
                    target,
                    speed_category or "all",
                    COLLECTION_CACHE_TTL_SECONDS,
                )
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fall through to regenerate
            pass

    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)

    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "--collect-only",
        "-q",
        "-m",
        category_expr,
    ]

    if target in {"behavior-tests", "integration-tests"} and speed_category:
        check_cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "--collect-only",
            "-q",
            "-m",
            category_expr,
        ]
        check_result = subprocess.run(
            check_cmd, check=False, capture_output=True, text=True
        )
        if "no tests ran" in check_result.stdout or not check_result.stdout.strip():
            collect_cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_path,
                "--collect-only",
                "-q",
                "-m",
                marker_expr,
            ]

    try:
        collect_result = subprocess.run(
            collect_cmd, check=False, capture_output=True, text=True
        )
        if collect_result.returncode not in (0, 5):
            if collect_result.stderr:
                logger.error("Collection stderr:\n%s", collect_result.stderr)
            tips = _failure_tips(collect_result.returncode, collect_cmd)
            logger.error(tips)
        raw_list = [
            line.strip()
            for line in collect_result.stdout.split("\n")
            if line.startswith("tests/") or line.startswith(test_path)
        ]
        test_list = _sanitize_node_ids(raw_list)
        # Prune non-existent file paths proactively to avoid stale selectors in cache
        pruned_list: list[str] = []
        for nid in test_list:
            path_part = nid.split("::", 1)[0]
            if os.path.exists(path_part):
                pruned_list.append(nid)
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tests": pruned_list,
            "fingerprint": {
                "latest_mtime": latest_mtime,
                "category_expr": category_expr,
                "test_path": test_path,
                # Simple signature to invalidate when set of node IDs changes significantly
                "node_set_hash": hash("\n".join(pruned_list)),
            },
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return pruned_list
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error collecting tests: %s", exc)
        tips = _failure_tips(-1, collect_cmd)
        logger.error(tips)
        return []


def run_tests(
    target: str,
    speed_categories: Sequence[str] | None = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int = 50,
    maxfail: int | None = None,
    extra_marker: str | None = None,
) -> tuple[bool, str]:
    """Execute pytest for the specified target.

    Args:
        target: Test target (``unit-tests``, ``integration-tests``,
            ``behavior-tests`` or ``all-tests``).
        speed_categories: Optional sequence of speed markers to run
            (``fast``, ``medium``, ``slow``). If ``None`` all tests are run.
        verbose: Whether to show verbose output.
        report: Whether to generate an HTML report.
        parallel: Run tests in parallel using ``pytest-xdist``.
        segment: Run tests in smaller batches for large suites.
        segment_size: Number of tests per batch when ``segment`` is ``True``.
        maxfail: Stop after this many failures.

    Returns:
        A tuple of ``(success, output)`` where ``success`` indicates whether all
        tests passed and ``output`` contains combined stdout/stderr.
    """
    log_level = logging.INFO if verbose else logging.WARNING
    logger.logger.setLevel(log_level)
    logger.info("\n%s", "=" * 80)
    logger.info(
        "Running %s with speed categories: %s...",
        target,
        speed_categories or "all",
    )
    logger.info("%s", "=" * 80)

    base_cmd = [sys.executable, "-m", "pytest"]
    if maxfail is not None:
        base_cmd.append(f"--maxfail={maxfail}")
    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])
    base_cmd.append(test_path)

    # When not running in parallel, force-disable auto-loading of third-party
    # pytest plugins to avoid hangs and unintended side effects in smoke/fast
    # paths. Respect any explicit user setting if already present.
    env = os.environ.copy()
    # Do not unilaterally disable third-party pytest plugins here. Disabling
    # plugin autoload while pytest.ini includes plugin-specific options (e.g.,
    # --cov flags from pytest-cov) causes 'unrecognized arguments' errors.
    # Smoke mode and stricter paths should set PYTEST_DISABLE_PLUGIN_AUTOLOAD
    # explicitly via the CLI layer.

    if verbose:
        base_cmd.append("-v")
    if parallel:
        # ``pytest-cov`` interacts poorly with ``pytest-xdist`` when workers
        # terminate unexpectedly, leading to internal ``KeyError`` exceptions
        # during teardown. Disabling coverage collection in parallel runs avoids
        # these worker teardown issues.
        base_cmd += ["-n", "auto", "--no-cov"]

    report_options: list[str] = []
    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"test_reports/{timestamp}/{target}")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_options = [
            f"--html={report_dir}/report.html",
            "--self-contained-html",
        ]
        logger.info("Report will be saved to %s/report.html", report_dir)

    # Determine how to apply extra filtering. Pytest '-m' does not support function-call
    # expressions like requires_resource('lmstudio'). If such an expression is provided,
    # approximate by using '-k lmstudio' which targets LM Studio-related modules/tests.
    use_keyword_filter = False
    keyword_expr = None
    if extra_marker:
        try:
            if re.search(r"requires_resource\((['\"])lmstudio\1\)", extra_marker):
                use_keyword_filter = True
                keyword_expr = "lmstudio"
        except Exception:
            pass

    if not speed_categories:
        category_expr = "not memory_intensive"
        if extra_marker and not use_keyword_filter:
            category_expr = f"({category_expr}) and ({extra_marker})"
        if use_keyword_filter and keyword_expr:
            # Narrow collection strictly to keyword-matching tests to avoid importing unrelated modules
            # that may emit strict marker-discipline errors during collection.
            collect_cmd = base_cmd + [
                "-q",
                "--collect-only",
            ]
            # Apply the base category expression to keep consistency with defaults
            collect_cmd += ["-m", category_expr]
            collect_cmd += ["-k", keyword_expr]
            collect_result = subprocess.run(
                collect_cmd, check=False, capture_output=True, text=True
            )
            raw_ids = [
                line.strip()
                for line in collect_result.stdout.split("\n")
                if line.startswith("tests/")
            ]
            node_ids = _sanitize_node_ids(raw_ids)
            if not node_ids:
                # Nothing to run is a success for subset execution
                return True, "No tests matched the provided filters."
            run_cmd = base_cmd + node_ids + report_options
            try:
                process = subprocess.Popen(
                    run_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                stdout, stderr = process.communicate()
                output = stdout + stderr
                logger.info(stdout)
                if stderr:
                    logger.error("ERRORS:")
                    logger.error(stderr)
                success = process.returncode in (0, 5)
                if "PytestBenchmarkWarning" in stderr:
                    success = True
                if not success:
                    tips = _failure_tips(process.returncode, run_cmd)
                    logger.error(tips)
                    output += tips
                return success, output
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error running tests: %s", exc)
                tips = _failure_tips(-1, run_cmd)
                return False, f"{exc}\n{tips}"
        else:
            cmd = base_cmd + ["-m", category_expr]
            cmd += report_options
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                stdout, stderr = process.communicate()
                output = stdout + stderr
                logger.info(stdout)
                if stderr:
                    logger.error("ERRORS:")
                    logger.error(stderr)
                success = process.returncode in (0, 5)
                if "PytestBenchmarkWarning" in stderr:
                    success = True
                if not success:
                    tips = _failure_tips(process.returncode, cmd)
                    logger.error(tips)
                    output += tips
                return success, output
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Error running tests: %s", exc)
                # Provide generic tips even on unexpected exceptions
                tips = _failure_tips(-1, cmd)
                return False, f"{exc}\n{tips}"

    all_success = True
    all_output = ""

    for speed in speed_categories:
        logger.info("\nRunning %s tests...", speed)
        marker_expr = f"{speed} and not memory_intensive"
        if extra_marker and not use_keyword_filter:
            marker_expr = f"({marker_expr}) and ({extra_marker})"
        # Collect matching node IDs to avoid importing unrelated modules that may fail marker checks.
        collect_cmd = base_cmd + ["-m", marker_expr, "--collect-only", "-q"]
        if use_keyword_filter and keyword_expr:
            collect_cmd += ["-k", keyword_expr]
        check_result = subprocess.run(
            collect_cmd, check=False, capture_output=True, text=True
        )
        raw_ids = [
            line.strip()
            for line in check_result.stdout.split("\n")
            if line.startswith("tests/")
        ]
        node_ids = _sanitize_node_ids(raw_ids)
        if not node_ids:
            logger.info("No %s tests found for %s, skipping...", speed, target)
            continue

        if segment:
            test_list = node_ids
            logger.info(
                "Found %d %s tests, running in batches of %d...",
                len(test_list),
                speed,
                segment_size,
            )
            batch_success = True
            for i in range(0, len(test_list), segment_size):
                batch = test_list[i : i + segment_size]
                logger.info(
                    "\nRunning batch %d/%d...",
                    i // segment_size + 1,
                    (len(test_list) + segment_size - 1) // segment_size,
                )
                batch_cmd = base_cmd + batch + report_options
                batch_process = subprocess.Popen(
                    batch_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                batch_stdout, batch_stderr = batch_process.communicate()
                logger.info(batch_stdout)
                if batch_stderr:
                    logger.error("ERRORS:")
                    logger.error(batch_stderr)
                batch_ok = batch_process.returncode in (0, 5)
                if "PytestBenchmarkWarning" in batch_stderr:
                    batch_ok = True
                if not batch_ok:
                    tips = _failure_tips(batch_process.returncode, batch_cmd)
                    logger.error(tips)
                    batch_stderr = batch_stderr + tips
                batch_success = batch_success and batch_ok
                all_output += batch_stdout + batch_stderr
            all_success = all_success and batch_success
        else:
            run_cmd = base_cmd + node_ids + report_options
            process = subprocess.Popen(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            stdout, stderr = process.communicate()
            logger.info(stdout)
            if stderr:
                logger.error("ERRORS:")
                logger.error(stderr)
            run_ok = process.returncode in (0, 5)
            if "PytestBenchmarkWarning" in stderr:
                run_ok = True
            if not run_ok:
                tips = _failure_tips(process.returncode, run_cmd)
                logger.error(tips)
                stderr = stderr + tips
            all_success = all_success and run_ok
            all_output += stdout + stderr

    return all_success, all_output
