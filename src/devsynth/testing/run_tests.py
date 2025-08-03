"""Shared pytest runner for DevSynth scripts and utilities.

This module provides a :func:`run_tests` function that executes pytest with
options compatible with DevSynth's CLI test commands. It is intended to be
reused by helper scripts such as ``scripts/run_all_tests.py`` and
``scripts/manual_cli_testing.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# Cache directory for test collection
COLLECTION_CACHE_DIR = ".test_collection_cache"

# Mapping of CLI targets to test paths
TARGET_PATHS = {
    "unit-tests": "tests/unit/",
    "integration-tests": "tests/integration/",
    "behavior-tests": "tests/behavior/",
    "all-tests": "tests/",
}


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
                print(
                    f"Using cached test collection for {target} ({speed_category or 'all'})"
                )
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            pass

    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)

    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "--collect-only",
        "-q",
    ]

    if target == "behavior-tests" and speed_category:
        check_cmd = collect_cmd + ["-m", speed_category]
        check_result = subprocess.run(
            check_cmd, check=False, capture_output=True, text=True
        )
        if "no tests ran" not in check_result.stdout and check_result.stdout.strip():
            collect_cmd.extend(["-m", speed_category])
    elif speed_category:
        collect_cmd.extend(["-m", speed_category])

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
        print(f"Error collecting tests: {exc}")
        return []


def run_tests(
    target: str,
    speed_categories: Optional[Sequence[str]] = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int = 50,
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

    Returns:
        A tuple of ``(success, output)`` where ``success`` indicates whether all
        tests passed and ``output`` contains combined stdout/stderr.
    """
    print(f"\n{'=' * 80}")
    print(f"Running {target} with speed categories: {speed_categories or 'all'}...")
    print(f"{'=' * 80}")

    base_cmd = [sys.executable, "-m", "pytest"]
    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])
    base_cmd.append(test_path)

    if verbose:
        base_cmd.append("-v")
    if parallel:
        base_cmd += ["-n", "auto"]

    report_options: List[str] = []
    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"test_reports/{timestamp}/{target}")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_options = [
            f"--html={report_dir}/report.html",
            "--self-contained-html",
        ]
        print(f"Report will be saved to {report_dir}/report.html")

    if not speed_categories:
        cmd = base_cmd + report_options
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            output = result.stdout + result.stderr
            print(result.stdout)
            if result.stderr:
                print("ERRORS:")
                print(result.stderr)
            return result.returncode == 0, output
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Error running tests: {exc}")
            return False, str(exc)

    all_success = True
    all_output = ""

    for speed in speed_categories:
        print(f"\nRunning {speed} tests...")
        if target == "behavior-tests":
            check_cmd = base_cmd + ["-m", speed, "--collect-only", "-q"]
            check_result = subprocess.run(
                check_cmd, check=False, capture_output=True, text=True
            )
            if "no tests ran" in check_result.stdout or not check_result.stdout.strip():
                print(
                    f"No behavior tests found with {speed} marker. Running all behavior tests..."
                )
                speed_cmd = base_cmd + report_options
            else:
                speed_cmd = base_cmd + ["-m", speed] + report_options
        else:
            speed_cmd = base_cmd + ["-m", speed] + report_options

        if segment:
            test_list = collect_tests_with_cache(target, speed)
            if not test_list:
                print(f"No {speed} tests found for {target}")
                continue

            print(
                f"Found {len(test_list)} {speed} tests, running in batches of {segment_size}..."
            )
            batch_success = True
            for i in range(0, len(test_list), segment_size):
                batch = test_list[i : i + segment_size]
                print(
                    f"\nRunning batch {i // segment_size + 1}/{(len(test_list) + segment_size - 1) // segment_size}..."
                )
                batch_cmd = base_cmd + ["-m", speed] + batch + report_options
                batch_result = subprocess.run(
                    batch_cmd, check=False, capture_output=True, text=True
                )
                print(batch_result.stdout)
                if batch_result.stderr:
                    print("ERRORS:")
                    print(batch_result.stderr)
                batch_success = batch_success and batch_result.returncode == 0
                all_output += batch_result.stdout + batch_result.stderr
            all_success = all_success and batch_success
        else:
            result = subprocess.run(
                speed_cmd, check=False, capture_output=True, text=True
            )
            print(result.stdout)
            if result.stderr:
                print("ERRORS:")
                print(result.stderr)
            all_success = all_success and result.returncode == 0
            all_output += result.stdout + result.stderr

    return all_success, all_output
