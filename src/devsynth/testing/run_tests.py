"""Shared pytest runner for DevSynth scripts and utilities.

This module provides a :func:`run_tests` function that executes pytest with
options compatible with DevSynth's CLI test commands. It is intended to be
intended for use by helper scripts such as ``scripts/manual_cli_testing.py``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass as _dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    NotRequired,
    TypedDict,
    cast,
    dataclass_transform,
)
from unittest.mock import patch
from uuid import uuid4

# Load sitecustomize early for Python 3.12+ compatibility patches
import sitecustomize  # noqa: F401
from devsynth.logging_setup import DevSynthLogger


# Lazy import release functions to avoid circular imports during basic test runs
def _import_release_functions() -> tuple[Any, Any, Any, Any]:
    """Lazy import release functions to avoid circular imports."""
    try:
        from devsynth.release import (
            compute_file_checksum,
            get_release_tag,
            publish_manifest,
            write_manifest,
        )

        return compute_file_checksum, get_release_tag, publish_manifest, write_manifest
    except ImportError:
        # If release module is not available due to circular imports,
        # provide stub implementations for basic functionality
        import hashlib
        from types import SimpleNamespace

        def compute_file_checksum_stub(path: Any) -> str:
            """Stub implementation for compute_file_checksum."""
            try:
                path_str = str(path)
                with open(path_str, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except (FileNotFoundError, OSError):
                return "stub_checksum"

        def get_release_tag_stub() -> str:
            """Stub implementation for get_release_tag."""
            return "v0.1.0a1"

        def publish_manifest_stub(manifest: Any) -> Any:
            """Stub implementation for publish_manifest."""
            # Return a mock object with expected attributes
            return SimpleNamespace(
                test_run_id="stub_test_run",
                quality_gate_id="stub_quality_gate",
                evidence_ids=("stub_evidence",),
                gate_status="stub_status",
                created={"stub": "created"},
                adapter_backend="stub_backend",
            )

        def write_manifest_stub(path: Any, manifest: Any) -> None:
            """Stub implementation for write_manifest."""
            pass

        return (
            compute_file_checksum_stub,
            get_release_tag_stub,
            publish_manifest_stub,
            write_manifest_stub,
        )


compute_file_checksum, get_release_tag, publish_manifest, write_manifest = (
    _import_release_functions()
)

# Cache directory for test collection
COLLECTION_CACHE_DIR = Path(".test_collection_cache")
TEST_COLLECTION_CACHE_FILE = COLLECTION_CACHE_DIR / "collection_cache.json"
# Standardized coverage outputs
COVERAGE_TARGET = "src/devsynth"
COVERAGE_JSON_PATH = Path("test_reports/coverage.json")
COVERAGE_HTML_DIR = Path("htmlcov")
LEGACY_HTML_DIRS: tuple[Path, ...] = (Path("test_reports/htmlcov"),)
PYTEST_COV_PLUGIN_MODULES: tuple[str, ...] = ("pytest_cov", "pytest_cov.plugin")
PYTEST_COV_PLUGIN_MISSING_MESSAGE = (
    "pytest plugin 'pytest_cov' not found. Install pytest-cov with "
    "`poetry add --group dev pytest-cov` or rerun "
    "`poetry install --with dev --extras tests` to restore coverage instrumentation."
)
PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE = (
    "pytest plugin autoload disabled without '-p pytest_cov'. Unset "
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 or append '-p pytest_cov' to PYTEST_ADDOPTS."
)
# Minimum aggregate coverage enforced for standard test runs.
#
# For alpha releases, use 70% threshold to balance quality with delivery velocity.
# For stable releases, use 90% to maintain high quality standards.
# This can be overridden via DEVSYNTH_COVERAGE_THRESHOLD environment variable.
DEFAULT_COVERAGE_THRESHOLD = 70.0


class PytestCovMissingError(RuntimeError):
    """Raised when pytest-cov instrumentation is required but unavailable."""


def _coverage_threshold() -> float:
    """Return the coverage threshold, honoring overrides via environment."""
    raw_value = os.environ.get("DEVSYNTH_COVERAGE_THRESHOLD")
    if raw_value is None or raw_value == "":
        return DEFAULT_COVERAGE_THRESHOLD

    try:
        parsed_value = float(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid DEVSYNTH_COVERAGE_THRESHOLD=%r; falling back to %.1f",
            raw_value,
            DEFAULT_COVERAGE_THRESHOLD,
        )
        return DEFAULT_COVERAGE_THRESHOLD

    if parsed_value <= 0 or parsed_value > 100:
        logger.warning(
            (
                "DEVSYNTH_COVERAGE_THRESHOLD must be between 0 and 100; got %s. "
                "Using default %.1f"
            ),
            raw_value,
            DEFAULT_COVERAGE_THRESHOLD,
        )
        return DEFAULT_COVERAGE_THRESHOLD

    return parsed_value


# TTL for collection cache in seconds (default: 3600); configurable via env var
try:
    COLLECTION_CACHE_TTL_SECONDS: int = int(
        os.environ.get("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "3600")
    )
except ValueError:
    # Fallback to default if malformed
    COLLECTION_CACHE_TTL_SECONDS = 3600

# Timeout for pytest collection subprocess. Reduced from 5 minutes to 60 seconds
# for faster feedback and to avoid hanging on collection issues.
DEFAULT_COLLECTION_TIMEOUT_SECONDS = 60.0


def _collection_timeout_seconds() -> float:
    """Return the collection timeout, honoring overrides via environment."""

    raw_value = os.environ.get("DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS")
    if raw_value is None or raw_value == "":
        return DEFAULT_COLLECTION_TIMEOUT_SECONDS

    try:
        parsed_value = float(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS=%r; falling back to %.1f",
            raw_value,
            DEFAULT_COLLECTION_TIMEOUT_SECONDS,
        )
        return DEFAULT_COLLECTION_TIMEOUT_SECONDS

    if parsed_value <= 0:
        logger.warning(
            (
                "DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS must be > 0; got %s. "
                "Using default %.1f"
            ),
            raw_value,
            DEFAULT_COLLECTION_TIMEOUT_SECONDS,
        )
        return DEFAULT_COLLECTION_TIMEOUT_SECONDS

    return parsed_value


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


def _coerce_int(value: object, default: int = 0) -> int:
    """Best-effort conversion of ``value`` to ``int``."""

    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


# Mapping of CLI targets to test paths
TARGET_PATHS: dict[str, str] = {
    "unit-tests": "tests/unit/",
    "integration-tests": "tests/integration/",
    "behavior-tests": "tests/behavior/",
    "all-tests": "tests/",
}

ALL_TESTS_DEPENDENCIES: tuple[str, ...] = (
    "unit-tests",
    "integration-tests",
    "behavior-tests",
)

logger = DevSynthLogger(__name__)

_RESOURCE_NAME_PATTERN = re.compile(r"requires_resource\((['\"])(?P<name>[^'\"]+)\1\)")
_RESOURCE_CALL_PATTERN = re.compile(
    r"^requires_resource\((['\"])(?P<name>[^'\"]+)\1\)$"
)


def _generate_metadata_id(prefix: str) -> str:
    """Return a unique identifier for execution metadata objects."""

    return f"{prefix}-{uuid4().hex}"


CommandVector = tuple[str, ...]
CommandMatrix = tuple[CommandVector, ...]


class BatchExecutionMetadata(TypedDict):
    """Metadata describing a single pytest batch execution."""

    metadata_id: str
    command: CommandVector
    returncode: int
    started_at: str
    completed_at: str
    coverage_enabled: bool
    coverage_issue: NotRequired[str]
    dry_run: NotRequired[bool]


class SegmentedRunMetadata(TypedDict):
    """Aggregated metadata describing a segmented pytest execution."""

    metadata_id: str
    commands: CommandMatrix
    returncode: int
    started_at: str | None
    completed_at: str | None
    segments: tuple[BatchExecutionMetadata, ...]


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    _RequestT = TypeVar("_RequestT")

    @dataclass_transform()
    def _slots_dataclass(
        *args: Any, **kwargs: Any
    ) -> Callable[[type[_RequestT]], type[_RequestT]]:
        """Typed wrapper that strips unsupported keywords during type checking."""

        kwargs.pop("slots", None)
        return _dataclass(*args, **kwargs)

else:
    _slots_dataclass = _dataclass


@_slots_dataclass(frozen=True, slots=True)
class SingleBatchRequest:
    """Structured configuration for a single pytest batch execution."""

    node_ids: tuple[str, ...]
    marker_expr: str
    verbose: bool
    report: bool
    parallel: bool
    maxfail: int | None
    keyword_filter: str | None
    env: dict[str, str]
    dry_run: bool = False

    def __post_init__(self) -> None:  # pragma: no cover - simple data normalization
        object.__setattr__(self, "node_ids", tuple(self.node_ids))


@_slots_dataclass(frozen=True, slots=True)
class SegmentedRunRequest:
    """Structured configuration for segmented pytest execution."""

    target: str
    speed_categories: tuple[str, ...]
    marker_expr: str
    node_ids: tuple[str, ...]
    verbose: bool
    report: bool
    parallel: bool
    segment_size: int
    maxfail: int | None
    keyword_filter: str | None
    env: dict[str, str]
    dry_run: bool = False

    def __post_init__(self) -> None:
        if self.segment_size <= 0:
            raise ValueError("segment_size must be a positive integer")
        object.__setattr__(self, "speed_categories", tuple(self.speed_categories))
        object.__setattr__(self, "node_ids", tuple(self.node_ids))


ExecutionMetadata = BatchExecutionMetadata | SegmentedRunMetadata
BatchExecutionResult = tuple[bool, str, BatchExecutionMetadata]
SegmentedRunResult = tuple[bool, str, SegmentedRunMetadata]


def ensure_coverage_output_directory() -> Path:
    """Create the coverage JSON output directory if it does not exist."""

    output_dir = COVERAGE_JSON_PATH.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _reset_coverage_artifacts() -> None:
    """Remove stale coverage artifacts before starting a test run."""

    ensure_coverage_output_directory()
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
        import importlib as _importlib

        _coverage_mod = _importlib.import_module("coverage")
        Coverage = getattr(_coverage_mod, "Coverage")
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

    # Skip coverage injection in smoke mode
    if env.get("DEVSYNTH_SMOKE_MODE") == "1":
        logger.debug(
            "pytest-cov injection skipped in smoke mode",
            extra={"pytest_addopts": env.get("PYTEST_ADDOPTS", "")},
        )
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
        (
            "Injected -p pytest_cov into PYTEST_ADDOPTS to preserve "
            "coverage instrumentation"
        ),
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
        (
            "Injected -p pytest_bdd.plugin into PYTEST_ADDOPTS to preserve "
            "pytest-bdd hooks"
        ),
        extra={"pytest_addopts": updated},
    )
    return True


def ensure_pytest_asyncio_plugin_env(env: MutableMapping[str, str]) -> bool:
    """Ensure pytest-asyncio loads when plugin autoloading is disabled."""

    if env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
        return False

    addopts_value = env.get("PYTEST_ADDOPTS", "")
    tokens = _parse_pytest_addopts(addopts_value)

    plugin_aliases = ("pytest_asyncio", "pytest_asyncio.plugin")
    if any(_plugin_explicitly_disabled(tokens, alias) for alias in plugin_aliases):
        logger.debug(
            (
                "pytest-asyncio remains disabled due to explicit "
                "-p no:pytest_asyncio override"
            ),
            extra={"pytest_addopts": addopts_value},
        )
        return False

    if _addopts_has_plugin(tokens, "pytest_asyncio"):
        return False

    normalized = addopts_value.strip()
    updated = f"-p pytest_asyncio.plugin {normalized}".strip()
    env["PYTEST_ADDOPTS"] = updated
    logger.info(
        (
            "Injected -p pytest_asyncio.plugin into PYTEST_ADDOPTS to preserve "
            "async test support"
        ),
        extra={"pytest_addopts": updated},
    )
    return True


def _pytest_cov_module_available() -> bool:
    """Return ``True`` when the pytest-cov plugin module is importable."""

    for module_name in PYTEST_COV_PLUGIN_MODULES:
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, AttributeError, ValueError):
            continue
        if spec is not None:
            return True
    return False


def pytest_cov_support_status(
    env: Mapping[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Determine whether pytest-cov instrumentation can be enabled."""

    mapping = env or os.environ
    addopts_value = mapping.get("PYTEST_ADDOPTS", "")
    tokens = _parse_pytest_addopts(addopts_value)

    if "--no-cov" in tokens:
        return (
            False,
            (
                "PYTEST_ADDOPTS contains --no-cov. Remove --no-cov to restore "
                "pytest-cov instrumentation."
            ),
        )
    if _addopts_has_plugin(tokens, "no:cov"):
        return (
            False,
            (
                "PYTEST_ADDOPTS disables pytest-cov via -p no:cov. Remove "
                "'-p no:cov' to restore coverage instrumentation."
            ),
        )
    if _addopts_has_plugin(tokens, "no:pytest_cov"):
        return (
            False,
            (
                "PYTEST_ADDOPTS disables pytest-cov via -p no:pytest_cov. Remove "
                "'-p no:pytest_cov' to restore coverage instrumentation."
            ),
        )

    autoload_disabled = mapping.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    if autoload_disabled:
        plugin_aliases = ("pytest_cov", "pytest_cov.plugin")
        if not any(_addopts_has_plugin(tokens, alias) for alias in plugin_aliases):
            return False, PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE

    if not _pytest_cov_module_available():
        return False, PYTEST_COV_PLUGIN_MISSING_MESSAGE

    return True, None


def _resolve_coverage_configuration(
    env: Mapping[str, str],
) -> tuple[list[str], bool, str | None]:
    """Build pytest coverage arguments based on plugin availability."""

    coverage_enabled, coverage_issue = pytest_cov_support_status(env)
    autoload_blocked = (
        not coverage_enabled and coverage_issue == PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE
    )
    if not coverage_enabled and not autoload_blocked:
        return [], coverage_enabled, coverage_issue

    coverage_arguments = [
        f"--cov={COVERAGE_TARGET}",
        f"--cov-report=json:{COVERAGE_JSON_PATH}",
        f"--cov-report=html:{COVERAGE_HTML_DIR}",
        "--cov-append",
    ]
    effective_enabled = coverage_enabled or autoload_blocked
    return coverage_arguments, effective_enabled, coverage_issue


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


def _archive_coverage_artifacts(
    *,
    release_tag: str,
    profile: str,
    timestamp: str,
    publication_message: str | None,
    execution_metadata: ExecutionMetadata,
) -> None:
    """Archive coverage artifacts under artifacts/releases/<tag>/<profile>/...

    Copies coverage.json, an htmlcov snapshot, and a small CLI log capturing
    the command and knowledge-graph banner. This keeps line lengths within
    our flake8 limit while documenting intent clearly.
    """
    try:
        dest_root = (
            Path("artifacts")
            / "releases"
            / release_tag
            / profile
            / f"{timestamp}-{profile}"
        )
        dest_root.mkdir(parents=True, exist_ok=True)
        # Copy JSON coverage
        try:
            shutil.copy2(COVERAGE_JSON_PATH, dest_root / "coverage.json")
        except Exception as exc:
            logger.warning("Archival: failed to copy coverage.json: %s", exc)
        # Copy HTML coverage directory as htmlcov-<timestamp>-<profile>
        html_dest = dest_root / f"htmlcov-{timestamp}-{profile}"
        try:
            if html_dest.exists():
                shutil.rmtree(html_dest)
            shutil.copytree(COVERAGE_HTML_DIR, html_dest)
        except Exception as exc:
            logger.warning("Archival: failed to copy HTML coverage directory: %s", exc)
        # Write a small log with the source command and banner message
        try:
            cmd_entries_raw = execution_metadata.get("commands")
            cmd_entries: list[Any] = []
            if isinstance(cmd_entries_raw, Sequence) and not isinstance(
                cmd_entries_raw, (str, bytes)
            ):
                cmd_entries = list(cmd_entries_raw)
            elif cmd_entries_raw is not None:
                cmd_entries = [str(cmd_entries_raw)]
            if not cmd_entries:
                primary = execution_metadata.get("command")
                cmd_entries = [str(primary)] if primary is not None else []
            command_strs: list[str] = []
            for entry in cmd_entries:
                if isinstance(entry, str):
                    command_strs.append(entry)
                elif isinstance(entry, Sequence) and not isinstance(
                    entry, (str, bytes)
                ):
                    command_strs.append(" ".join(str(p) for p in entry))
                elif entry is not None:
                    command_strs.append(str(entry))
            log_text = []
            if command_strs:
                log_text.append("Command(s):\n" + "\n".join(command_strs))
            if publication_message:
                log_text.append("\n" + publication_message)
            (dest_root / f"devsynth_run_tests_{profile}.log").write_text(
                "\n".join(log_text) or ""
            )
        except Exception as exc:
            logger.warning("Archival: failed to write CLI log: %s", exc)
    except Exception:
        logger.debug("Archival step encountered an error", exc_info=True)


def _maybe_publish_coverage_evidence(
    *,
    report: bool,
    success: bool,
    marker_fallback: bool,
    execution_metadata: ExecutionMetadata,
    normalized_speeds: list[str],
    collected_node_ids: list[str],
) -> str | None:
    """Publish coverage run outputs to the knowledge graph when possible."""

    if not report or not success or marker_fallback:
        return None

    artifacts_ok, reason = coverage_artifacts_status()
    if not artifacts_ok:
        logger.warning("Skipping release graph publication: %s", reason)
        return f"[knowledge-graph] coverage ingestion skipped: {reason}"

    try:
        coverage_payload = json.loads(COVERAGE_JSON_PATH.read_text())
    except Exception as exc:
        logger.error("Unable to parse coverage JSON for graph ingestion: %s", exc)
        return f"[knowledge-graph] coverage ingestion failed: invalid JSON ({exc})"

    totals = (
        coverage_payload.get("totals") if isinstance(coverage_payload, dict) else None
    )
    raw_percent = None
    if isinstance(totals, dict):
        raw_percent = totals.get("percent_covered")
    if not isinstance(raw_percent, (int, float)):
        return "[knowledge-graph] coverage ingestion failed: percent_covered missing"
    coverage_percent = float(raw_percent)

    html_index = COVERAGE_HTML_DIR / "index.html"
    if not html_index.exists():
        return f"[knowledge-graph] coverage ingestion failed: missing {html_index}"

    try:
        coverage_checksum = compute_file_checksum(COVERAGE_JSON_PATH)
        html_checksum = compute_file_checksum(html_index)
    except OSError as exc:
        logger.error("Unable to compute coverage artifact checksum: %s", exc)
        return f"[knowledge-graph] coverage ingestion failed: checksum error ({exc})"

    commands_raw = execution_metadata.get("commands")
    command_entries: list[object] = []
    if isinstance(commands_raw, Sequence) and not isinstance(
        commands_raw, (str, bytes)
    ):
        command_entries = list(commands_raw)
    elif commands_raw is not None:
        command_entries = [commands_raw]

    if not command_entries:
        primary_command = execution_metadata.get("command")
        if isinstance(primary_command, Sequence) and not isinstance(
            primary_command, (str, bytes)
        ):
            command_entries = [list(primary_command)]
        elif isinstance(primary_command, str):
            command_entries = [primary_command]
        elif primary_command is not None:
            command_entries = [primary_command]

    command_strings: list[str] = []
    for entry in command_entries:
        if isinstance(entry, str):
            command_strings.append(entry)
        elif isinstance(entry, Sequence) and not isinstance(entry, (str, bytes)):
            command_strings.append(" ".join(str(part) for part in entry))
        else:
            command_strings.append(str(entry))

    source_command = " && ".join(command_strings) if command_strings else ""

    started_raw = execution_metadata.get("started_at")
    completed_raw = execution_metadata.get("completed_at")
    started_at = (
        str(started_raw)
        if isinstance(started_raw, (str, datetime))
        else datetime.now(UTC).isoformat()
    )
    completed_at = (
        str(completed_raw)
        if isinstance(completed_raw, (str, datetime))
        else datetime.now(UTC).isoformat()
    )
    exit_code = _coerce_int(execution_metadata.get("returncode", 0))

    if exit_code not in (0, 5):
        gate_status = "blocked"
    elif coverage_percent >= _coverage_threshold():
        gate_status = "pass"
    else:
        gate_status = "fail"

    checksum_builder = hashlib.sha256()
    checksum_builder.update(
        "|".join(sorted(normalized_speeds or ["all"])).encode("utf-8")
    )
    checksum_builder.update(str(coverage_percent).encode("utf-8"))
    checksum_builder.update(str(len(collected_node_ids)).encode("utf-8"))
    checksum_builder.update(str(exit_code).encode("utf-8"))
    checksum_builder.update(coverage_checksum.encode("utf-8"))
    checksum_builder.update(html_checksum.encode("utf-8"))
    run_checksum = checksum_builder.hexdigest()

    profile = "+".join(normalized_speeds) if normalized_speeds else "all"
    release_tag = get_release_tag()
    evaluated_at = datetime.now(UTC).isoformat()
    manifest = {
        "run_type": "coverage",
        "release_tag": release_tag,
        "source_command": source_command,
        "artifacts": [
            {
                "artifact_type": "coverage_json",
                "path": str(COVERAGE_JSON_PATH),
                "checksum": coverage_checksum,
                "collected_at": completed_at,
            },
            {
                "artifact_type": "coverage_html",
                "path": str(html_index),
                "checksum": html_checksum,
                "collected_at": completed_at,
            },
        ],
        "test_run": {
            "profile": profile,
            "coverage_percent": coverage_percent,
            "tests_collected": len(collected_node_ids),
            "exit_code": exit_code,
            "started_at": started_at,
            "completed_at": completed_at,
            "run_checksum": run_checksum,
            "metadata": {
                "commands": command_strings,
                "artifact_checksums": [coverage_checksum, html_checksum],
            },
        },
        "quality_gate": {
            "gate_name": "coverage",
            "threshold": _coverage_threshold(),
            "status": gate_status,
            "evaluated_at": evaluated_at,
            "metadata": {
                "coverage_percent": coverage_percent,
                "tests_collected": len(collected_node_ids),
            },
        },
    }

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest_dir = COVERAGE_JSON_PATH.parent
    manifest_path = manifest_dir / f"coverage_manifest_{timestamp}.json"
    latest_manifest_path = manifest_dir / "coverage_manifest_latest.json"
    write_manifest(manifest_path, manifest)
    write_manifest(latest_manifest_path, manifest)

    try:
        publication = publish_manifest(manifest)
    except Exception as exc:
        logger.error("Release graph publication failed: %s", exc)
        return f"[knowledge-graph] coverage ingestion failed: {exc}"

    raw_release_flags = publication.created.get("release_evidence", [])
    evidence_created: Sequence[object]
    if isinstance(raw_release_flags, Sequence) and not isinstance(
        raw_release_flags, (str, bytes)
    ):
        evidence_created = raw_release_flags
    else:
        evidence_created = ()
    evidence_parts = []
    for evidence_id, created in zip(publication.evidence_ids, evidence_created):
        suffix = " (new)" if bool(created) else ""
        evidence_parts.append(f"{evidence_id}{suffix}")
    evidence_summary = ", ".join(evidence_parts)

    test_run_state = "new" if bool(publication.created.get("test_run")) else "updated"
    gate_state = "new" if bool(publication.created.get("quality_gate")) else "updated"

    publication_message = (
        "[knowledge-graph] coverage gate "
        f"{publication.gate_status} → QualityGate "
        f"{publication.quality_gate_id} ({gate_state}), "
        f"TestRun {publication.test_run_id} ({test_run_state}), "
        f"Evidence [{evidence_summary}] via {publication.adapter_backend}; "
        f"coverage={coverage_percent:.2f}% "
        f"threshold={_coverage_threshold():.2f}%"
    )

    # Archive artifacts under artifacts/releases/<tag>/<profile>/<timestamp>-<profile>/
    try:
        _archive_coverage_artifacts(
            release_tag=release_tag,
            profile=profile,
            timestamp=timestamp,
            publication_message=publication_message,
            execution_metadata=execution_metadata,
        )
    except Exception:
        logger.debug("Archival step failed", exc_info=True)

    return publication_message


def enforce_coverage_threshold(
    coverage_file: Path | str = COVERAGE_JSON_PATH,
    minimum_percent: float | None = None,
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

    threshold = (
        minimum_percent if minimum_percent is not None else _coverage_threshold()
    )
    if percent_value < threshold:
        message = (
            f"Coverage {percent_value:.2f}% is below the required " f"{threshold:.2f}%"
        )
        logger.error(message)
        if exit_on_failure:
            raise SystemExit(1)
        raise RuntimeError(message)

    logger.info("Coverage %.2f%% meets the %.2f%% threshold.", percent_value, threshold)
    return percent_value


def _sanitize_node_ids(ids: Sequence[str]) -> list[str]:
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


def _normalize_keyword_filter(keyword_filter: str | None) -> str | None:
    """Normalize keyword filters for cache fingerprints."""

    if keyword_filter is None:
        return None
    normalized = " ".join(keyword_filter.split())
    return normalized or None


def _cache_key_suffix(keyword_filter: str | None) -> str:
    """Return a filesystem-safe suffix for cache keys."""

    if not keyword_filter:
        return ""
    digest = hashlib.sha256(keyword_filter.encode("utf-8")).hexdigest()
    return f"kw-{digest[:16]}"


def _strip_resource_markers(marker_expr: str) -> str:
    """Remove ``requires_resource`` calls from a marker expression."""

    if not marker_expr.strip():
        return ""

    tokens = re.split(r"(\band\b|\bor\b)", marker_expr)
    cleaned_parts: list[str] = []
    pending_connector: str | None = None

    for token in tokens:
        stripped = token.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered in {"and", "or"}:
            pending_connector = lowered
            continue
        if _RESOURCE_CALL_PATTERN.match(stripped):
            pending_connector = None
            continue
        if pending_connector and cleaned_parts:
            cleaned_parts.append(pending_connector)
        pending_connector = None
        cleaned_parts.append(stripped)

    return " ".join(cleaned_parts).strip()


def _latest_mtime(root: str) -> float:
    """Return the most recent mtime for Python sources under ``root``."""

    latest = 0.0
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                try:
                    mtime = os.path.getmtime(os.path.join(dirpath, fn))
                except OSError:
                    continue
                if mtime > latest:
                    latest = mtime
    return latest


def _log_collection_cache_event(
    event: str,
    *,
    target: str,
    speed_category: str | None,
    cache_file: Path,
    keyword_filter: str | None,
    ttl_seconds: int,
    reason: str | None = None,
) -> None:
    """Emit structured diagnostics for cache activity."""

    message = f"test collection cache {event} for target=%s (%s)"
    if reason:
        message += f" — {reason}"
    logger.info(
        message,
        target,
        speed_category or "all",
        extra={
            "event": f"test_collection_cache_{event}",
            "target": target,
            "speed_category": speed_category or "all",
            "cache_file": str(cache_file),
            "keyword_filter": keyword_filter,
            "cache_ttl_seconds": ttl_seconds,
            "reason": reason,
        },
    )


def _collect_via_pytest(
    *,
    target: str,
    test_path: str,
    category_expr: str,
    normalized_filter: str | None,
    timeout_seconds: float,
) -> list[str]:
    """Execute ``pytest --collect-only`` and return node identifiers."""

    # Use the same Python executable that poetry is using
    # Check for poetry's active python first, then fallback to virtual env python
    python_exe = os.environ.get("POETRY_ACTIVE_PYTHON")
    if not python_exe:
        # Try to find the virtual environment python
        venv_python = Path.cwd() / ".venv" / "bin" / "python3"
        if venv_python.exists():
            python_exe = str(venv_python)
        else:
            python_exe = sys.executable
    collect_cmd = [
        python_exe,
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

    if normalized_filter:
        collect_cmd.extend(["-k", normalized_filter])

    # Get the project root (where pyproject.toml is located)
    project_root = Path(__file__).parent.parent.parent.parent

    # Inherit the full environment but override specific variables for collection
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTEST_PLUGINS"] = "pytest_bdd.plugin"
    env["PYTEST_ADDOPTS"] = "-p pytest_bdd.plugin"

    result = subprocess.run(
        collect_cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        cwd=str(project_root),  # Ensure subprocess runs from project root
        env=env,  # Inherit environment but override key variables
    )
    if result.returncode != 0:
        if result.stderr:
            error_message = f"Test collection failed: {result.stderr}"
        else:
            error_message = f"Test collection failed with exit code {result.returncode}"

        # Log more details for debugging
        logger.warning(
            error_message,
            extra={
                "event": "test_collection_failed",
                "target": target,
                "returncode": result.returncode,
                "stdout": (
                    result.stdout[:500] if result.stdout else None
                ),  # First 500 chars
                "stderr": (
                    result.stderr[:500] if result.stderr else None
                ),  # First 500 chars
                "speed_category": category_expr,
            },
        )
        raise RuntimeError(error_message)

    node_ids: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and "::" in line and not line.startswith("="):
            node_ids.append(line)

    return _sanitize_node_ids(node_ids)


def _collect_dependent_targets(
    *,
    dependencies: Sequence[str],
    speed_category: str | None,
    keyword_filter: str | None,
    timeout_seconds: float,
) -> tuple[list[str], list[str]]:
    """Collect tests for dependent targets and return (nodes, timeouts)."""

    aggregated: list[str] = []
    seen: set[str] = set()
    timed_out: list[str] = []

    for dependency in dependencies:
        try:
            nodes = collect_tests_with_cache(
                dependency,
                speed_category,
                keyword_filter=keyword_filter,
                _allow_all_target_decomposition=False,
                _timeout_override=timeout_seconds,
                _propagate_timeout=True,
            )
        except RuntimeError:
            # Propagate runtime failures so callers can surface actionable tips.
            raise
        except subprocess.TimeoutExpired:
            timed_out.append(dependency)
            continue

        for node in nodes:
            if node not in seen:
                seen.add(node)
                aggregated.append(node)

    return aggregated, timed_out


def collect_tests_with_cache(
    target: str,
    speed_category: str | None = None,
    *,
    keyword_filter: str | None = None,
    _allow_all_target_decomposition: bool = True,
    _timeout_override: float | None = None,
    _propagate_timeout: bool = False,
) -> list[str]:
    """Collect tests for the given target and speed category.

    Args:
        target: Logical test target such as ``unit-tests`` or ``all-tests``.
        speed_category: Optional speed marker used to scope collection.
        keyword_filter: Optional ``-k`` expression applied during collection.

    Returns:
        A list of pytest node identifiers matching the requested filters.
    """
    test_path = TARGET_PATHS.get(target, TARGET_PATHS["all-tests"])

    # Build the marker expression we'll use and compute a simple fingerprint of
    # the test tree (latest mtime) to detect changes that should invalidate cache.
    marker_expr = "not memory_intensive"
    category_expr = marker_expr
    if speed_category:
        category_expr = f"{speed_category} and {marker_expr}"

    normalized_filter = _normalize_keyword_filter(keyword_filter)
    latest_mtime = _latest_mtime(test_path)
    base_cache_key = f"{target}_{speed_category or 'all'}"
    suffix = _cache_key_suffix(normalized_filter)
    cache_key = f"{base_cache_key}_{suffix}" if suffix else base_cache_key
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
            stored_keyword_filter = cached_data.get("fingerprint", {}).get(
                "keyword_filter"
            )

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
                and (stored_keyword_filter == normalized_filter)
            )

            if (
                cache_time
                and (datetime.now() - cache_time).total_seconds()
                < COLLECTION_CACHE_TTL_SECONDS
                and fingerprint_matches
            ):
                _log_collection_cache_event(
                    "hit",
                    target=target,
                    speed_category=speed_category,
                    cache_file=cache_file,
                    keyword_filter=normalized_filter,
                    ttl_seconds=COLLECTION_CACHE_TTL_SECONDS,
                )
                return cast(list[str], cached_data["tests"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("Error loading test collection cache: %s", e)
            # Fall through to regenerate
            pass

    COLLECTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)  # Use Path method
    collection_timeout = _timeout_override or _collection_timeout_seconds()

    dependencies: tuple[str, ...] = ()
    if (
        target == "all-tests"
        and _allow_all_target_decomposition
        and ALL_TESTS_DEPENDENCIES
    ):
        # Skip behavior tests in smoke mode to avoid collection timeouts
        if os.environ.get("DEVSYNTH_SMOKE_MODE") == "1":
            dependencies = ("unit-tests", "integration-tests")
        else:
            dependencies = ALL_TESTS_DEPENDENCIES

    node_ids: list[str] = []
    dependency_timeouts: list[str] = []

    if dependencies:
        _log_collection_cache_event(
            "miss",
            target=target,
            speed_category=speed_category,
            cache_file=cache_file,
            keyword_filter=normalized_filter,
            ttl_seconds=COLLECTION_CACHE_TTL_SECONDS,
            reason="decomposing all-tests into dependent targets",
        )
        node_ids, dependency_timeouts = _collect_dependent_targets(
            dependencies=dependencies,
            speed_category=speed_category,
            keyword_filter=keyword_filter,
            timeout_seconds=collection_timeout,
        )
    else:
        _log_collection_cache_event(
            "miss",
            target=target,
            speed_category=speed_category,
            cache_file=cache_file,
            keyword_filter=normalized_filter,
            ttl_seconds=COLLECTION_CACHE_TTL_SECONDS,
            reason="collecting via pytest",
        )

    if not node_ids:
        try:
            node_ids = _collect_via_pytest(
                target=target,
                test_path=test_path,
                category_expr=category_expr,
                normalized_filter=normalized_filter,
                timeout_seconds=collection_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            logger.warning(
                "Test collection timeout for target=%s (%s); falling back to path",
                target,
                speed_category or "all",
                extra={
                    "event": "test_collection_timeout",
                    "target": target,
                    "speed_category": speed_category or "all",
                    "keyword_filter": normalized_filter,
                    "dependencies": list(dependencies),
                },
            )
            if dependencies and dependency_timeouts:
                logger.info(
                    "Re-attempted dependent collections before timeout fallback",
                    extra={
                        "event": "test_collection_timeout_retry",
                        "target": target,
                        "timed_out_dependencies": dependency_timeouts,
                        "keyword_filter": normalized_filter,
                    },
                )
            if _propagate_timeout:
                raise exc
            return []
        except OSError as exc:
            logger.warning("Test collection failed: %s", exc)
            return []

    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "tests": node_ids,
        "fingerprint": {
            "latest_mtime": latest_mtime,
            "category_expr": category_expr,
            "test_path": test_path,
            "keyword_filter": normalized_filter,
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
    *,
    dry_run: bool = False,
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

    ensure_coverage_output_directory()

    if dry_run:
        logger.info("Dry run requested; skipping coverage artifact cleanup")
    else:
        # Reset coverage artifacts
        _reset_coverage_artifacts()

    # Ensure coverage plugins are available
    # Skip coverage injection in smoke mode (detected by DEVSYNTH_SMOKE_MODE)
    if env.get("DEVSYNTH_SMOKE_MODE") != "1":
        ensure_pytest_cov_plugin_env(env)

    # Skip BDD and asyncio plugin injection in smoke mode to avoid collection timeouts
    if env.get("DEVSYNTH_SMOKE_MODE") != "1":
        ensure_pytest_bdd_plugin_env(env)
        ensure_pytest_asyncio_plugin_env(env)

    # Pre-initialize pytest-bdd to avoid CONFIG_STACK issues when plugin
    # autoloading is disabled
    if env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1":
        try:
            import pytest_bdd

            # Force initialization of pytest-bdd configuration stack
            if hasattr(pytest_bdd.scenario, "CONFIG_STACK"):
                _ = len(
                    pytest_bdd.scenario.CONFIG_STACK
                )  # Access CONFIG_STACK to ensure it's initialized
        except (ImportError, AttributeError):
            pass  # pytest-bdd not available or already initialized

    coverage_ready, coverage_issue = pytest_cov_support_status(env)
    if not coverage_ready and coverage_issue == PYTEST_COV_PLUGIN_MISSING_MESSAGE:
        message = f"[coverage] {coverage_issue}"
        logger.error(
            "pytest-cov plugin unavailable; aborting test run",
            extra={"coverage_issue": coverage_issue},
        )
        raise PytestCovMissingError(message)

    # Normalize requested speed categories; default to fast+medium for parity
    # with the repository-wide pytest.ini when no explicit speeds are provided.
    normalized_speeds: list[str] = []
    if speed_categories:
        for category in speed_categories:
            if category not in normalized_speeds:
                normalized_speeds.append(category)
    else:
        normalized_speeds = ["fast", "medium"]

    # Build marker expression with deterministic ordering.
    marker_parts = ["not memory_intensive"]
    if normalized_speeds:
        if len(normalized_speeds) == 1:
            marker_parts.append(normalized_speeds[0])
        else:
            speed_expr = " or ".join(normalized_speeds)
            marker_parts.append(f"({speed_expr})")

    extra_marker_value = extra_marker or ""
    cleaned_extra_marker = extra_marker_value
    effective_keyword_filter = keyword_filter
    if effective_keyword_filter is None and extra_marker_value:
        resource_matches = [
            match.group("name")
            for match in _RESOURCE_NAME_PATTERN.finditer(extra_marker_value)
        ]
        if resource_matches:
            unique_resources = list(dict.fromkeys(resource_matches))
            effective_keyword_filter = " and ".join(unique_resources)
            cleaned_extra_marker = _strip_resource_markers(extra_marker_value)
    allow_gui_env = os.environ.get("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", "false")
    allow_gui = allow_gui_env.strip().lower() in {"1", "true", "yes", "on"}
    gui_requested = "gui" in extra_marker_value or "webui" in extra_marker_value
    if cleaned_extra_marker:
        marker_parts.append(f"({cleaned_extra_marker})")
    if not allow_gui and not gui_requested:
        marker_parts.append("not gui")

    marker_expr = " and ".join(marker_parts)

    # Validate target
    if target not in TARGET_PATHS:
        raise ValueError(
            f"Unknown test target: '{target}'. "
            f"Available targets are: {', '.join(TARGET_PATHS.keys())}"
        )

    # Collect tests for each requested speed category and merge results.
    collected_node_ids: list[str] = []
    collect_callable = collect_tests_with_cache
    try:
        collect_signature = inspect.signature(collect_callable)
    except (TypeError, ValueError):  # pragma: no cover - fallback for builtins
        supports_keyword_filter = True
    else:
        supports_keyword_filter = "keyword_filter" in collect_signature.parameters

    try:
        if normalized_speeds:
            for category in normalized_speeds:
                if supports_keyword_filter:
                    nodes = collect_callable(
                        target,
                        category,
                        keyword_filter=effective_keyword_filter,
                    )
                else:  # pragma: no cover - compatibility for patched callables
                    nodes = collect_callable(target, category)
                collected_node_ids.extend(nodes)
        else:
            if supports_keyword_filter:
                nodes = collect_callable(
                    target,
                    None,
                    keyword_filter=effective_keyword_filter,
                )
            else:  # pragma: no cover - compatibility for patched callables
                nodes = collect_callable(target, None)
            collected_node_ids.extend(nodes)
    except RuntimeError as e:
        return False, str(e)

    # Deduplicate node identifiers while preserving order so marker filtering
    # can run once per unique test path.
    deduped_nodes: list[str] = []
    seen_nodes: set[str] = set()
    for node in collected_node_ids:
        if node not in seen_nodes:
            seen_nodes.add(node)
            deduped_nodes.append(node)
    collected_node_ids = deduped_nodes

    marker_fallback = False
    if not collected_node_ids:
        logger.info(
            "marker fallback triggered for target=%s (speeds=%s)",
            target,
            ",".join(normalized_speeds or ["all"]),
        )
        marker_fallback = True
        collected_node_ids = [TARGET_PATHS[target]]

    execution_metadata: ExecutionMetadata
    if segment and normalized_speeds and not marker_fallback:
        # Segmented execution
        segmented_request = SegmentedRunRequest(
            target=target,
            speed_categories=tuple(normalized_speeds),
            marker_expr=marker_expr,
            node_ids=tuple(collected_node_ids),
            verbose=verbose,
            report=report,
            parallel=parallel,
            segment_size=segment_size or 50,
            maxfail=maxfail,
            keyword_filter=effective_keyword_filter,
            env=env,
            dry_run=dry_run,
        )
        success, output, execution_metadata = _run_segmented_tests(segmented_request)
    else:
        # Single execution
        batch_request = SingleBatchRequest(
            node_ids=tuple(collected_node_ids),
            marker_expr=marker_expr,
            verbose=verbose,
            report=report,
            parallel=parallel,
            maxfail=maxfail,
            keyword_filter=effective_keyword_filter,
            env=env,
            dry_run=dry_run,
        )
        success, output, execution_metadata = _run_single_test_batch(batch_request)
        if not dry_run:
            _ensure_coverage_artifacts()

    if marker_fallback:
        output = "Marker fallback executed.\n" + output

    if dry_run:
        return success, output

    publication_message = _maybe_publish_coverage_evidence(
        report=report,
        success=success,
        marker_fallback=marker_fallback,
        execution_metadata=execution_metadata,
        normalized_speeds=normalized_speeds,
        collected_node_ids=collected_node_ids,
    )
    if publication_message:
        output = f"{output.rstrip()}\n{publication_message}\n"

    return success, output


def _run_segmented_tests(request: SegmentedRunRequest) -> SegmentedRunResult:
    """Run tests in segments to handle large test suites."""

    sanitized_node_ids = tuple(_sanitize_node_ids(request.node_ids))
    all_outputs: list[str] = []
    segment_metadata: list[BatchExecutionMetadata] = []
    overall_success = True

    segments: tuple[CommandVector, ...] = tuple(
        sanitized_node_ids[i : i + request.segment_size]
        for i in range(0, len(sanitized_node_ids), request.segment_size)
    )

    logger.info(
        "Running %d tests in %d segments of size %d for target=%s",
        len(sanitized_node_ids),
        len(segments),
        request.segment_size,
        request.target,
    )

    for index, segment_nodes in enumerate(segments):
        if not segment_nodes:
            continue

        logger.info(
            "Running segment %d/%d (%d tests)",
            index + 1,
            len(segments),
            len(segment_nodes),
        )

        batch_request = SingleBatchRequest(
            node_ids=segment_nodes,
            marker_expr=request.marker_expr,
            verbose=request.verbose,
            report=request.report and (index == len(segments) - 1),
            parallel=request.parallel,
            maxfail=request.maxfail,
            keyword_filter=request.keyword_filter,
            env=request.env,
            dry_run=request.dry_run,
        )
        success, output, batch_metadata = _run_single_test_batch(batch_request)

        all_outputs.append(output)
        segment_metadata.append(batch_metadata)
        if not success:
            overall_success = False
            if request.maxfail:
                break  # Stop on first failure if maxfail is set

    if not request.dry_run:
        _ensure_coverage_artifacts()

    combined_metadata: SegmentedRunMetadata
    if segment_metadata:
        first_meta = segment_metadata[0]
        last_meta = segment_metadata[-1]
        commands: CommandMatrix = tuple(meta["command"] for meta in segment_metadata)
        combined_metadata = {
            "metadata_id": _generate_metadata_id("segmented"),
            "commands": commands,
            "returncode": last_meta["returncode"],
            "started_at": first_meta["started_at"],
            "completed_at": last_meta["completed_at"],
            "segments": tuple(segment_metadata),
        }
    else:
        now_iso = datetime.now(UTC).isoformat()
        combined_metadata = {
            "metadata_id": _generate_metadata_id("segmented"),
            "commands": tuple(),
            "returncode": -1,
            "started_at": now_iso,
            "completed_at": now_iso,
            "segments": tuple(),
        }

    return overall_success, "\n".join(all_outputs), combined_metadata


def _run_single_test_batch(request: SingleBatchRequest) -> BatchExecutionResult:
    """Run a single batch of tests."""

    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend(request.node_ids)
    cmd.extend(["-m", request.marker_expr])

    coverage_args, coverage_enabled, coverage_issue = _resolve_coverage_configuration(
        request.env
    )
    if coverage_enabled:
        cmd.extend(coverage_args)

    if request.verbose:
        cmd.append("-v")
    if request.parallel:
        cmd.extend(["-n", "auto"])
    if request.maxfail:
        cmd.extend(["--maxfail", str(request.maxfail)])
    if request.keyword_filter:
        cmd.extend(["-k", request.keyword_filter])

    # Ensure sitecustomize is loaded for Python 3.12+ compatibility
    src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    current_pythonpath = request.env.get("PYTHONPATH", "")
    if src_path not in current_pythonpath:
        request.env["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"

    if request.env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1":
        addopts = request.env.get("PYTEST_ADDOPTS", "")
        tokens = _parse_pytest_addopts(addopts)
        additions: list[str] = []
        if coverage_enabled and not any(
            _addopts_has_plugin(tokens, alias)
            for alias in ("pytest_cov", "pytest_cov.plugin")
        ):
            additions.append("-p pytest_cov")
        if not any(
            _addopts_has_plugin(tokens, alias)
            for alias in ("pytest_bdd", "pytest_bdd.plugin")
        ):
            additions.append("-p pytest_bdd")
        if not any(
            _addopts_has_plugin(tokens, alias)
            for alias in ("pytest_asyncio", "pytest_asyncio.plugin")
        ):
            additions.append("-p pytest_asyncio.plugin")
        if additions:
            normalized = addopts.strip()
            request.env["PYTEST_ADDOPTS"] = (
                f"{' '.join(additions)} {normalized}".strip()
            )

    try:
        started_at = datetime.now(UTC)
        command_preview = shlex.join(cmd)
        logger.debug("Running command: %s", command_preview)

        if request.dry_run:
            completed_at = datetime.now(UTC)
            dry_run_metadata: BatchExecutionMetadata = {
                "metadata_id": _generate_metadata_id("batch"),
                "command": tuple(cmd),
                "returncode": 0,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "coverage_enabled": coverage_enabled,
                "dry_run": True,
            }
            if coverage_issue:
                dry_run_metadata["coverage_issue"] = coverage_issue
            logger.info("Dry run preview (no execution): %s", command_preview)
            lines = [
                "Dry run: pytest invocation prepared but not executed.",
                f"Command: {command_preview}",
            ]
            if coverage_issue:
                lines.append(f"Coverage instrumentation note: {coverage_issue}")
            return True, "\n".join(lines) + "\n", dry_run_metadata

        # Ensure PYTHONPATH is set for subprocess to load sitecustomize
        env = request.env.copy()
        src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        current_pythonpath = env.get("PYTHONPATH", "")
        if src_path not in current_pythonpath:
            env["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        output, _ = process.communicate()
        completed_at = datetime.now(UTC)
        success = process.returncode in (0, 5)

        if not success:
            output += _failure_tips(process.returncode, cmd)

        metadata: BatchExecutionMetadata = {
            "metadata_id": _generate_metadata_id("batch"),
            "command": tuple(cmd),
            "returncode": int(process.returncode or 0),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "coverage_enabled": coverage_enabled,
        }
        if coverage_issue:
            metadata["coverage_issue"] = coverage_issue
        return success, output, metadata
    except Exception as exc:
        error_msg = f"Failed to run tests: {exc}"
        logger.error(error_msg)
        now_iso = datetime.now(UTC).isoformat()
        return (
            False,
            error_msg,
            {
                "metadata_id": _generate_metadata_id("batch"),
                "command": tuple(cmd),
                "returncode": -1,
                "started_at": now_iso,
                "completed_at": now_iso,
                "coverage_enabled": False,
            },
        )


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
    enforce_coverage_threshold(
        coverage_file, minimum_percent=90.0, exit_on_failure=False
    )
    print("    - Success case passed.")

    # Test failure
    coverage_file.write_text(json.dumps({"totals": {"percent_covered": 75.0}}))
    try:
        enforce_coverage_threshold(
            coverage_file, minimum_percent=80.0, exit_on_failure=False
        )
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
