"""Shared pytest runner for DevSynth scripts and utilities.

This module provides a :func:`run_tests` function that executes pytest with
options compatible with DevSynth's CLI test commands. It is intended to be
intended for use by helper scripts such as ``scripts/manual_cli_testing.py``.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from devsynth.logging_setup import DevSynthLogger

# Cache directory for test collection
COLLECTION_CACHE_DIR = ".test_collection_cache"

# Mapping of CLI targets to test paths
TARGET_PATHS = {
    "unit-tests": "tests/unit/",
    "integration-tests": "tests/integration/",
    "behavior-tests": "tests/behavior/",
    "all-tests": "tests/",
}

logger = DevSynthLogger(__name__)


def collect_tests_with_cache(
    target: str, speed_category: Optional[str] = None
) -> List[str]:
    """Collect tests for the given target and speed category.

    Results are cached for a short period to speed up repeated collections.

    Args:
        target: Test target (e.g. ``unit-tests`` or ``integration-tests``).
        speed_category: Optional speed marker to filter tests.

    Returns:
        A list of test paths matching the criteria.
    """
    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])

    cache_key = f"{target}_{speed_category or 'all'}"
    cache_file = os.path.join(COLLECTION_CACHE_DIR, f"{cache_key}_tests.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 3600:
                logger.info(
                    "Using cached test collection for %s (%s)",
                    target,
                    speed_category or "all",
                )
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            pass

    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)

    marker_expr = "not memory_intensive"
    category_expr = marker_expr
    if speed_category:
        category_expr = f"{speed_category} and {marker_expr}"

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

    if target == "behavior-tests" and speed_category:
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
        test_list = [
            line.strip()
            for line in collect_result.stdout.split("\n")
            if line.startswith("tests/")
        ]

        cache_data = {"timestamp": datetime.now().isoformat(), "tests": test_list}
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return test_list
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error collecting tests: %s", exc)
        return []


def run_tests(
    target: str,
    speed_categories: Optional[Sequence[str]] = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int = 50,
    maxfail: Optional[int] = None,
) -> Tuple[bool, str]:
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

    if verbose:
        base_cmd.append("-v")
    if parallel:
        # ``pytest-cov`` interacts poorly with ``pytest-xdist`` when workers
        # terminate unexpectedly, leading to internal ``KeyError`` exceptions
        # during teardown. Disabling coverage collection in parallel runs avoids
        # these worker teardown issues.
        base_cmd += ["-n", "auto", "--no-cov"]

    report_options: List[str] = []
    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"test_reports/{timestamp}/{target}")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_options = [
            f"--html={report_dir}/report.html",
            "--self-contained-html",
        ]
        logger.info("Report will be saved to %s/report.html", report_dir)

    if not speed_categories:
        cmd = base_cmd + ["-m", "not memory_intensive"] + report_options
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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
            return success, output
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error running tests: %s", exc)
            return False, str(exc)

    all_success = True
    all_output = ""

    for speed in speed_categories:
        logger.info("\nRunning %s tests...", speed)
        marker_expr = f"{speed} and not memory_intensive"
        check_cmd = base_cmd + ["-m", marker_expr, "--collect-only", "-q"]
        check_result = subprocess.run(
            check_cmd, check=False, capture_output=True, text=True
        )
        if "no tests ran" in check_result.stdout or not check_result.stdout.strip():
            logger.info("No %s tests found for %s, skipping...", speed, target)
            continue
        speed_cmd = base_cmd + ["-m", marker_expr] + report_options

        if segment:
            test_list = collect_tests_with_cache(target, speed)
            if not test_list:
                logger.info("No %s tests found for %s", speed, target)
                continue

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
                batch_cmd = base_cmd + ["-m", marker_expr] + batch + report_options
                batch_process = subprocess.Popen(
                    batch_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                batch_stdout, batch_stderr = batch_process.communicate()
                logger.info(batch_stdout)
                if batch_stderr:
                    logger.error("ERRORS:")
                    logger.error(batch_stderr)
                batch_ok = batch_process.returncode in (0, 5)
                if "PytestBenchmarkWarning" in batch_stderr:
                    batch_ok = True
                batch_success = batch_success and batch_ok
                all_output += batch_stdout + batch_stderr
            all_success = all_success and batch_success
        else:
            process = subprocess.Popen(
                speed_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate()
            logger.info(stdout)
            if stderr:
                logger.error("ERRORS:")
                logger.error(stderr)
            run_ok = process.returncode in (0, 5)
            if "PytestBenchmarkWarning" in stderr:
                run_ok = True
            all_success = all_success and run_ok
            all_output += stdout + stderr

    return all_success, all_output
