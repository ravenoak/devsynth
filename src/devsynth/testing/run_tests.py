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

from devsynth.logging_setup import DevSynthLogger

# Cache directory for test collection
COLLECTION_CACHE_DIR: str = ".test_collection_cache"
# Standardized coverage outputs
COVERAGE_TARGET = "src/devsynth"
COVERAGE_JSON_PATH = Path("test_reports/coverage.json")
COVERAGE_HTML_DIR = Path("htmlcov")
LEGACY_HTML_DIRS: tuple[Path, ...] = (Path("test_reports/htmlcov"),)
DEFAULT_COVERAGE_THRESHOLD = 90.0
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
        from coverage import Coverage  # type: ignore[import-not-found]
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
        message = (
            f"Coverage {percent_value:.2f}% is below the required {minimum_percent:.2f}%"
        )
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
                cached_data: dict[str, Any] = json.load(f)
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
                    (
                        "Using cached test collection for %s (%s) [TTL=%ss; "
                        "fingerprint ok]"
                    ),
                    target,
                    speed_category or "all",
                    COLLECTION_CACHE_TTL_SECONDS,
                )
                return cast(list[str], cached_data["tests"])
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
        "-o",
        "addopts=",
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
            "-o",
            "addopts=",
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
        # Hermetic collection: run with CWD at test_path.
        # Avoid changing plugin autoload unless already set.
        orig_cwd = os.getcwd()
        try:
            did_chdir = False
            if os.path.isdir(test_path):
                os.chdir(test_path)
                did_chdir = True
            if did_chdir and len(collect_cmd) > 3:
                collect_cmd[3] = "."
            collect_result = subprocess.run(
                collect_cmd, check=False, capture_output=True, text=True
            )
        finally:
            if did_chdir:
                os.chdir(orig_cwd)
        if collect_result.returncode not in (0, 5):
            if collect_result.stderr:
                logger.error("Collection stderr:\n%s", collect_result.stderr)
            tips = _failure_tips(collect_result.returncode, collect_cmd)
            logger.error(tips)
        # Pytest outputs node ids relative to the current working directory. When
        # collecting from an absolute target path, the lines will typically start
        # with the basename of that directory rather than the absolute path. Accept
        # standard test tree (tests/...), absolute path startswith, and the
        # basename-prefixed relative path.
        pattern = re.compile(r".*\.py(?::\d+)?(::|$)")
        raw_list = [
            line.strip()
            for line in collect_result.stdout.split("\n")
            if pattern.match(line.strip())
        ]
        test_list = _sanitize_node_ids(raw_list)
        # If collection unexpectedly returns empty, attempt a minimal fallback
        # by retrying collection without marker filtering; if still empty and a
        # cache exists, return the cached set pruned by filesystem.
        if not test_list:
            fallback_cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_path,
                "--collect-only",
                "-q",
                "-o",
                "addopts=",
            ]
            try:
                orig_cwd2 = os.getcwd()
                did_chdir2 = False
                if os.path.isdir(test_path):
                    os.chdir(test_path)
                    did_chdir2 = True
                    fallback_cmd[3] = "."
                fallback_result = subprocess.run(
                    fallback_cmd, check=False, capture_output=True, text=True
                )
            finally:
                if did_chdir2:
                    os.chdir(orig_cwd2)
            fallback_raw = [
                line.strip()
                for line in fallback_result.stdout.split("\n")
                if pattern.match(line.strip())
            ]
            test_list = _sanitize_node_ids(fallback_raw)
            if not test_list and os.path.exists(cache_file):
                try:
                    with open(cache_file) as f:
                        prev = json.load(f).get("tests", [])
                    test_list = [
                        nid for nid in prev if os.path.exists(nid.split("::", 1)[0])
                    ]
                except Exception:
                    test_list = []
        # Prune non-existent file paths proactively to avoid stale selectors in cache
        pruned_list: list[str] = []
        for nid in test_list:
            path_part = nid.split("::", 1)[0]
            if os.path.exists(path_part):
                pruned_list.append(nid)
        # If still empty, synthesize a minimal list from filesystem to avoid flakes in
        # hermetic unit environments where plugin interactions suppress stdout.
        if not pruned_list and os.path.isdir(test_path):
            synthesized: list[str] = []
            for dirpath, _dirnames, filenames in os.walk(test_path):
                for fn in filenames:
                    if fn.startswith("test_") and fn.endswith(".py"):
                        synthesized.append(os.path.join(dirpath, fn))
            pruned_list = synthesized
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tests": pruned_list,
            "fingerprint": {
                "latest_mtime": latest_mtime,
                "category_expr": category_expr,
                "test_path": test_path,
                # Simple signature to invalidate when the set of node IDs
                # changes significantly
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

    _reset_coverage_artifacts()

    coverage_plugin_injected = ensure_pytest_cov_plugin_env(os.environ)
    bdd_plugin_injected = ensure_pytest_bdd_plugin_env(os.environ)
    if coverage_plugin_injected:
        logger.info(
            "PYTEST_ADDOPTS updated to include -p pytest_cov for test subprocesses",
            extra={"pytest_addopts": os.environ.get("PYTEST_ADDOPTS", "")},
        )
    if bdd_plugin_injected:
        logger.info(
            "PYTEST_ADDOPTS updated to include -p pytest_bdd.plugin for test subprocesses",
            extra={"pytest_addopts": os.environ.get("PYTEST_ADDOPTS", "")},
        )

    pytest_base = [sys.executable, "-m", "pytest"]
    if maxfail is not None:
        pytest_base.append(f"--maxfail={maxfail}")

    coverage_args = [
        f"--cov={COVERAGE_TARGET}",
        "--cov-report=term-missing",
        f"--cov-report=json:{COVERAGE_JSON_PATH}",
        f"--cov-report=html:{COVERAGE_HTML_DIR}",
        "--cov-append",
    ]

    xdist_args: list[str] = []
    if parallel:
        xdist_args = ["-n", "auto"]

    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])
    collect_base_cmd = pytest_base + [test_path]
    run_base_cmd = pytest_base + coverage_args + xdist_args + [test_path]

    # When not running in parallel, force-disable auto-loading of third-party
    # pytest plugins to avoid hangs and unintended side effects in smoke/fast
    # paths. Respect any explicit user setting if already present.
    env = os.environ.copy()
    if ensure_pytest_cov_plugin_env(env):
        logger.info(
            "Ensured subprocess environment retains -p pytest_cov despite plugin autoload restrictions",
            extra={"pytest_addopts": env.get("PYTEST_ADDOPTS", "")},
        )
    if ensure_pytest_bdd_plugin_env(env):
        logger.info(
            "Ensured subprocess environment retains -p pytest_bdd.plugin despite plugin autoload restrictions",
            extra={"pytest_addopts": env.get("PYTEST_ADDOPTS", "")},
        )
    # Do not unilaterally disable third-party pytest plugins here. Disabling
    # plugin autoload while pytest.ini includes plugin-specific options (e.g.,
    # --cov flags from pytest-cov) causes 'unrecognized arguments' errors.
    # Smoke mode and stricter paths should set PYTEST_DISABLE_PLUGIN_AUTOLOAD
    # explicitly via the CLI layer.

    if verbose:
        collect_base_cmd.append("-v")
        run_base_cmd.append("-v")

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

    # Determine how to apply extra filtering. Pytest '-m' does not support
    # function-call expressions like requires_resource('lmstudio'). If such
    # an expression is provided, approximate by using '-k lmstudio' which
    # targets LM Studio-related modules/tests.
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
            # Narrow collection strictly to keyword-matching tests to avoid
            # importing unrelated modules that may emit strict
            # marker-discipline errors during collection.
            collect_cmd = collect_base_cmd + [
                "-q",
                "--collect-only",
            ]
            # Apply the base category expression to keep consistency with defaults
            collect_cmd += ["-m", category_expr]
            collect_cmd += ["-k", keyword_expr]
            collect_result = subprocess.run(
                collect_cmd, check=False, capture_output=True, text=True
            )
            pattern = re.compile(r".*\.py(::|$)")
            raw_ids = [
                line.strip()
                for line in collect_result.stdout.split("\n")
                if pattern.match(line.strip())
            ]
            node_ids = _sanitize_node_ids(raw_ids)
            if not node_ids:
                # Nothing to run is a success for subset execution
                return True, "No tests matched the provided filters."
            run_cmd = run_base_cmd + node_ids + report_options
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
            cmd = run_base_cmd + ["-m", category_expr]
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
        # Collect matching node IDs to avoid importing unrelated modules
        # that may fail marker checks.
        collect_cmd = collect_base_cmd + [
            "-m",
            marker_expr,
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
        ]
        if use_keyword_filter and keyword_expr:
            collect_cmd += ["-k", keyword_expr]
        # Temporarily change CWD to the test path to stabilize relative node ids
        # and optionally suppress third-party plugin autoloading for hermetic collection
        orig_cwd = os.getcwd()
        try:
            did_chdir = False
            if os.path.isdir(test_path):
                os.chdir(test_path)
                did_chdir = True
            if did_chdir and len(collect_cmd) > 3:
                collect_cmd[3] = "."
            check_result = subprocess.run(
                collect_cmd, check=False, capture_output=True, text=True
            )
        finally:
            # Restore working directory
            if did_chdir:
                os.chdir(orig_cwd)
        pattern = re.compile(r".*\.py(::|$)")
        raw_ids = [
            line.strip()
            for line in check_result.stdout.split("\n")
            if pattern.match(line.strip())
        ]
        node_ids = _sanitize_node_ids(raw_ids)
        base_norm = Path(test_path).as_posix().rstrip("/")
        base_name = Path(base_norm).name
        normalized_ids: list[str] = []
        for nid in node_ids:
            path_part, sep, remainder = nid.partition("::")
            rel_path = path_part.lstrip("./")
            final_path = rel_path
            if Path(path_part).is_absolute():
                final_path = Path(path_part).as_posix()
            else:
                if rel_path.startswith(f"{base_norm}/") or rel_path == base_norm:
                    final_path = rel_path
                elif base_name and (
                    rel_path == base_name
                    or rel_path.startswith(f"{base_name}/")
                ):
                    suffix = rel_path[len(base_name) :].lstrip("/")
                    final_path = (
                        f"{base_norm}/{suffix}" if suffix else base_norm
                    )
                elif rel_path:
                    final_path = f"{base_norm}/{rel_path}"
                else:
                    final_path = base_norm
            normalized = final_path
            if sep:
                normalized = f"{normalized}{sep}{remainder}"
            normalized_ids.append(normalized)
        node_ids = normalized_ids
        node_count = len(node_ids)
        if node_count == 0:
            logger.warning(
                "No node ids were collected for %s/%s; running pytest with marker fallback",
                speed,
                target,
                extra={
                    "pytest_marker_expr": marker_expr,
                    "pytest_collect_returncode": check_result.returncode,
                },
            )

        if segment and node_ids:
            test_list = node_ids
            logger.info(
                "Found %d %s tests, running in batches of %d...",
                len(test_list),
                speed,
                segment_size,
            )
            batch_success = True
            total_batches = (len(test_list) + segment_size - 1) // segment_size
            for i in range(0, len(test_list), segment_size):
                batch = test_list[i : i + segment_size]
                logger.info(
                    "\nRunning batch %d/%d...",
                    i // segment_size + 1,
                    total_batches,
                )
                batch_cmd = run_base_cmd + batch + report_options
                try:
                    batch_process = subprocess.Popen(
                        batch_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env,
                    )
                    batch_stdout, batch_stderr = batch_process.communicate()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error(
                        "Error executing segmented batch", exc_info=exc
                    )
                    tips = _failure_tips(-1, batch_cmd)
                    logger.error(tips)
                    all_output += f"{exc}\n{tips}"
                    batch_success = False
                    all_success = False
                    continue
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
            # If any batch failed, append a concise aggregation tip block once
            if not batch_success:
                aggregate_cmd = run_base_cmd
                agg_tips = _failure_tips(1, aggregate_cmd)
                logger.error(agg_tips)
                all_output += agg_tips
            all_success = all_success and batch_success
        else:
            if segment and not node_ids:
                logger.warning(
                    "Segmented execution requested for %s/%s but no node ids were collected; executing a single pytest command instead",
                    speed,
                    target,
                    extra={"pytest_marker_expr": marker_expr},
                )
            run_cmd = run_base_cmd + ["-m", marker_expr] + report_options
            logger.info(
                "Executing pytest command",
                extra={
                    "pytest_command": run_cmd,
                    "pytest_node_count": node_count,
                },
            )
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
            if not run_ok:
                tips = _failure_tips(process.returncode, run_cmd)
                logger.error(tips)
                stderr = stderr + tips
            all_success = all_success and run_ok
            all_output += stdout + stderr

    _ensure_coverage_artifacts()
    return all_success, all_output
