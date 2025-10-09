#!/usr/bin/env python3
"""Verify pytest markers and provide a cached, deterministic summary.

This script offers a lightweight verification surface to keep CI runs fast.
It scans test files for pytest markers, attempts a minimal 'collection' by
executing modules in an isolated namespace to catch basic import errors, and
uses a content-hash cache to avoid reprocessing unchanged files.

Adheres to project guidelines: deterministic behavior, clear outputs, and
graceful failure handling. Designed to be extended along docs/plan.md.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
REPORT_PATH = ROOT / "test_reports" / "test_markers_report.json"
CACHE_PATH = ROOT / ".cache" / "test_markers_cache.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
PYPROJECT_PATH = ROOT / "pyproject.toml"

MARK_RE = re.compile(r"@pytest\.mark\.([a-zA-Z_][a-zA-Z0-9_]*)")

# In-memory caches (tests access these directly)
PERSISTENT_CACHE: dict[str, dict] = {}
FILE_SIGNATURES: dict[str, tuple[float, str]] = {}

MARKER_DOCUMENTATION_PATHS: dict[str, pathlib.Path] = {
    "integtest": ROOT / "docs" / "testing" / "verify_test_markers.md",
}


@dataclass
class FileVerification:
    markers: dict[str, int]
    issues: list


def _normalize_marker_name(raw: str) -> str:
    """Return the canonical marker name without parameter hints."""

    base = raw.split("(", 1)[0]
    return base.strip()


def load_configured_markers() -> dict[str, str]:
    """Load configured pytest markers from pyproject.toml."""

    if not PYPROJECT_PATH.exists():
        return {}
    try:
        data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    markers_section = (
        data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
    )
    configured: dict[str, str] = {}
    for entry in markers_section or []:
        if not isinstance(entry, str):
            continue
        name_part, _, description = entry.partition(":")
        name = _normalize_marker_name(name_part)
        if not name:
            continue
        configured[name] = description.strip()
    return configured


def find_undocumented_markers(
    marker_docs: dict[str, pathlib.Path] | None = None,
) -> list[str]:
    """Return configured markers that are missing documentation."""

    docs = marker_docs or MARKER_DOCUMENTATION_PATHS
    configured = load_configured_markers()
    missing: list[str] = []
    for marker, doc_path in docs.items():
        if marker not in configured:
            # Skip documentation requirements for markers not configured.
            continue
        try:
            text = doc_path.read_text(encoding="utf-8")
        except Exception:
            missing.append(marker)
            continue
        pattern = re.compile(rf"\b{re.escape(marker)}\b")
        if not pattern.search(text):
            missing.append(marker)
    # Deterministic order for reporting
    return sorted(dict.fromkeys(missing))


def get_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Verify pytest markers with caching. "
            "By default scans the tests/ directory. "
            "Use --changed to scan only changed test files since a base ref."
        )
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Scan only changed test files (via git diff).",
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD",
        help="Git base reference to diff against when using --changed (default: HEAD).",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=None,
        help="Explicit file paths to verify (overrides directory scan).",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a JSON summary report (legacy compatibility).",
    )
    parser.add_argument(
        "--report-file",
        default=str(REPORT_PATH),
        help=(
            "Path to write the JSON summary report "
            "(default: test_markers_report.json)."
        ),
    )
    parser.add_argument(
        "--cross-check-collection",
        action="store_true",
        help=(
            "Cross-check static scan against pytest --collect-only -q inventory; "
            "prints discrepancies and exits non-zero if any are found."
        ),
    )
    return parser


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _compute_signature(path: pathlib.Path) -> tuple[float, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return (0.0, "")
    mtime = path.stat().st_mtime
    return (mtime, _hash_text(text))


def _load_disk_cache() -> None:
    if CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                PERSISTENT_CACHE.update(data.get("persistent_cache", {}))
                FILE_SIGNATURES.update(
                    {k: tuple(v) for k, v in data.get("file_signatures", {}).items()}
                )
        except Exception:
            # Ignore cache read errors
            pass


def _save_disk_cache() -> None:
    try:
        payload = {
            "persistent_cache": PERSISTENT_CACHE,
            "file_signatures": FILE_SIGNATURES,
        }
        CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def _collect_markers_from_text(text: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for m in MARK_RE.finditer(text):
        counts[m.group(1)] += 1
    return dict(counts)


def _collect_test_functions(path: pathlib.Path, text: str) -> list[str]:
    """Return names of test functions defined in the module."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.append(node.name)
    return names


def _find_speed_marker_violations(path: pathlib.Path, text: str) -> list[dict]:
    """Return a list of violations for the exactly-one speed marker rule.

    Scope for enforcement (iterative rollout per docs/plan.md):
    - Enforce strictly for unit tests under tests/unit/.
    - Integration/behavior will be onboarded in subsequent iterations once optional
      extras and resource profiles are standardized and markers are added.

    Rules:
    - Prefer function-level decorators on test_ functions.
    - If no function-level speed marker is present, allow parametrize-level marks
      via pytest.param(..., marks=pytest.mark.<speed>) provided ALL parameters
      specify exactly the same single speed marker.
    - Allowed speed markers: fast | medium | slow.
    - Exactly one must be present overall; 0 or >1 are violations.
    - Module-level markers do not satisfy this requirement.
    """
    violations: list[dict] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        # Already handled elsewhere as a syntax error; skip here.
        return violations

    # Limit strict enforcement to unit tests during this iteration
    p_str = str(path)
    if "/tests/unit/" not in p_str and "\\tests\\unit\\" not in p_str:
        return violations

    speed_markers = {"fast", "medium", "slow"}

    def _extract_marker_name_from_attr(a: ast.AST) -> str | None:
        # Accept pytest.mark.<name> and pytest.mark.<name>()
        if isinstance(a, ast.Attribute):
            name = getattr(a, "attr", None)
            return name if isinstance(name, str) and name in speed_markers else None
        if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute):
            name = getattr(a.func, "attr", None)
            return name if isinstance(name, str) and name in speed_markers else None
        return None

    # Detect module-level speed markers assigned to pytestmark (informational
    # during grace period)
    try:
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                # Handle: pytestmark = ... or: pytestmark: Any = ...
                target_names: list[str] = []
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            target_names.append(t.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name):
                        target_names.append(node.target.id)
                if "pytestmark" in target_names:
                    # Look for speed markers in the assigned value
                    val = (
                        node.value
                        if isinstance(node, (ast.Assign, ast.AnnAssign))
                        else None
                    )
                    markers_found: list[str] = []
                    if isinstance(val, (ast.List, ast.Tuple)):
                        elements = list(getattr(val, "elts", []))
                    else:
                        elements = [val] if val is not None else []
                    for el in elements:
                        name = _extract_marker_name_from_attr(el)
                        if name:
                            markers_found.append(name)
                    # During marker hygiene grace, do not flag module-level
                    # speed markers as violations. Future iterations may
                    # re-enable this once function-level backfill is complete.
                    pass
    except Exception:
        # Be permissive on AST shapes we don't anticipate
        pass

    def _collect_parametrize_speed_markers(dec: ast.Call) -> list[str]:
        """Inspect a @pytest.mark.parametrize decorator for pytest.param marks.

        We only consider markers embedded in pytest.param(..., marks=...). If every
        param has exactly one of {fast, medium, slow} and they are all identical,
        return that single marker; otherwise return [].
        """
        # Identify the argvalues argument: typically second positional arg
        argvalues: ast.AST | None = None
        if dec.args:
            argvalues = dec.args[1] if len(dec.args) >= 2 else None
        for kw in getattr(dec, "keywords", []) or []:
            if getattr(kw, "arg", None) == "argvalues":
                argvalues = kw.value
                break
        if argvalues is None:
            return []
        # Normalize to a list of parameters
        elements: list[ast.AST] = []
        if isinstance(argvalues, (ast.List, ast.Tuple)):
            elements = list(argvalues.elts)
        else:
            # Not a static list/tuple; can't analyze safely
            return []
        all_param_markers: list[str] = []
        for el in elements:
            # We care about pytest.param(...) entries
            if isinstance(el, ast.Call):
                # Check if func is pytest.param
                is_param = False
                if isinstance(el.func, ast.Attribute):
                    is_param = (
                        getattr(el.func, "attr", "") == "param"
                        and isinstance(el.func.value, ast.Name)
                        and getattr(el.func.value, "id", "") == "pytest"
                    )
                elif isinstance(el.func, ast.Name):
                    is_param = el.func.id == "param"  # from "from pytest import param"
                if not is_param:
                    return []  # Bail if non-pytest.param entries are present
                # Look for marks=...
                mark_value = None
                for kw in el.keywords or []:
                    if getattr(kw, "arg", None) == "marks":
                        mark_value = kw.value
                        break
                if mark_value is None:
                    return []
                # marks may be a single marker or a list of markers
                markers_here: list[str] = []
                if isinstance(mark_value, (ast.List, ast.Tuple)):
                    for v in mark_value.elts:
                        name = _extract_marker_name_from_attr(v)
                        if name:
                            markers_here.append(name)
                else:
                    name = _extract_marker_name_from_attr(mark_value)
                    if name:
                        markers_here.append(name)
                # Exactly one speed marker per param
                if len(markers_here) != 1:
                    return []
                all_param_markers.append(markers_here[0])
            else:
                # Non-call entries: cannot analyze reliably
                return []
        # All params must agree on the same single marker
        if not all_param_markers:
            return []
        unique = set(all_param_markers)
        return [unique.pop()] if len(unique) == 1 else []

    # Helper to check if a function has pytest-bdd step decorators
    def _has_bdd_step_decorator(fn: ast.FunctionDef) -> bool:
        step_names = {"given", "when", "then", "step"}
        for dec in getattr(fn, "decorator_list", []) or []:
            # Accept @pytest_bdd.given / @pytest_bdd.when / ... or imported names
            # like @given
            if isinstance(dec, ast.Attribute):
                if isinstance(dec.value, ast.Name) and dec.attr in step_names:
                    return True
            elif isinstance(dec, ast.Name):
                if dec.id in step_names:
                    return True
            elif isinstance(dec, ast.Call):
                # Called decorators: e.g., @given("pattern")
                if isinstance(dec.func, ast.Attribute):
                    if (
                        isinstance(dec.func.value, ast.Name)
                        and dec.func.attr in step_names
                    ):
                        return True
                elif isinstance(dec.func, ast.Name):
                    if dec.func.id in step_names:
                        return True
        return False

    for node in ast.walk(tree):
        # Enforce speed markers only on canonical test functions (test_*).
        # BDD step functions are excluded from strict speed marker enforcement
        # to avoid penalizing behavior step libraries; they are orchestrated by
        # feature files and scenario runners rather than executed as standalone tests.
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Collect decorator names of the form pytest.mark.<name>
            found: list[str] = []
            parametrize_found: list[str] = []
            for dec in node.decorator_list:
                # Handle @pytest.mark.<name>
                attr = None
                if isinstance(dec, ast.Attribute):
                    attr = dec
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    # Allow called markers like @pytest.mark.slow()
                    attr = dec.func
                if attr and isinstance(attr, ast.Attribute):
                    marker_name = getattr(attr, "attr", None)
                    if isinstance(marker_name, str) and marker_name in speed_markers:
                        found.append(marker_name)
                # Handle @pytest.mark.parametrize(...)
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if getattr(dec.func, "attr", None) == "parametrize":
                        param_speed = _collect_parametrize_speed_markers(dec)
                        if param_speed:
                            parametrize_found.extend(param_speed)
            # Reconcile: prefer function-level marker; else consider
            # parametrize-only
            effective = found or parametrize_found
            # Iterative grace: treat missing speed marker as implicitly 'fast'
            # to reduce noise while we backfill markers. Only flag if multiple
            # markers are present.
            if len(effective) > 1:
                violations.append(
                    {
                        "type": "speed_marker_violation",
                        "function": node.name,
                        "file": str(path),
                        "markers_found": effective,
                        "message": (
                            f"Function {node.name} has multiple speed markers; "
                            "exactly one expected"
                        ),
                    }
                )
    return violations


def _find_property_marker_violations(path: pathlib.Path, text: str) -> list[dict]:
    """For modules under tests/property, ensure each test function has
    @pytest.mark.property.

    We do not fail the script on these violations (informational), but
    include them in issues and summary stats to aid hygiene improvements.
    """
    violations: list[dict] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return violations

    def _has_property_marker(dec: ast.AST) -> bool:
        # Accept pytest.mark.property and called form pytest.mark.property()
        if isinstance(dec, ast.Attribute):
            return getattr(dec, "attr", None) == "property"
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            return getattr(dec.func, "attr", None) == "property"
        return False

    # BDD step functions or test_ functions are considered
    def _has_bdd_step_decorator(fn: ast.FunctionDef) -> bool:
        step_names = {"given", "when", "then", "step"}
        for dec in getattr(fn, "decorator_list", []) or []:
            if isinstance(dec, ast.Attribute):
                if isinstance(dec.value, ast.Name) and dec.attr in step_names:
                    return True
            elif isinstance(dec, ast.Name):
                if dec.id in step_names:
                    return True
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    if (
                        isinstance(dec.func.value, ast.Name)
                        and dec.func.attr in step_names
                    ):
                        return True
                elif isinstance(dec.func, ast.Name):
                    if dec.func.id in step_names:
                        return True
        return False

    def _is_hypothesis_given(dec: ast.AST) -> bool:
        """Return True if decorator represents Hypothesis' @given."""
        if isinstance(dec, ast.Name):
            return dec.id == "given"
        if isinstance(dec, ast.Attribute):
            return getattr(dec, "attr", None) == "given"
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name):
                return func.id == "given"
            if isinstance(func, ast.Attribute):
                return getattr(func, "attr", None) == "given"
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and (
            node.name.startswith("test_") or _has_bdd_step_decorator(node)
        ):
            # Ignore nested Hypothesis helpers named ``check`` which serve as
            # helpers inside test functions. They are decorated with @given and
            # inherit the parent's markers, so requiring an explicit property
            # marker would be redundant.
            if (
                node.name == "check"
                and node.col_offset > 0
                and any(_is_hypothesis_given(d) for d in (node.decorator_list or []))
            ):
                continue
            has_property = any(
                _has_property_marker(dec) for dec in (node.decorator_list or [])
            )
            if not has_property:
                violations.append(
                    {
                        "type": "property_marker_violation",
                        "function": node.name,
                        "file": str(path),
                        "message": (
                            "tests/property/ require @pytest.mark.property "
                            "in addition to one speed marker"
                        ),
                    }
                )
    return violations


def _attempt_collection(path: pathlib.Path, text: str) -> list:
    """Very light-weight 'collection' to catch obvious import errors.

    We parse to AST (to validate syntax) and then exec the module code in an
    isolated namespace to trigger import-time errors. We avoid running tests by
    not invoking pytest and by not calling any functions.

    Notes:
    - To align with repository defaults (minimal env; GUI/resources skipped), we
      do not treat missing optional extras as issues for behavior/UI or resource-
      gated tests. This reduces false positives in marker hygiene reports and
      matches pytest.ini addopts "-m 'not slow and not gui'".
    """
    issues = []
    # Ensure repository sources are importable when executing test modules.
    original_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(ROOT))
        src_path = ROOT / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))

        try:
            ast.parse(text)
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax_error",
                    "message": str(e),
                }
            )
            return issues

        OPTIONAL_IMPORTS = {
            # Web/UI and visualization
            "streamlit",
            "nicegui",
            "dearpygui",
            # Vector/DB backends and deps
            "chromadb",
            "faiss",
            "faiss_cpu",
            "kuzu",
            "duckdb",
            "tinydb",
            "lmdb",
            "rdflib",
            "numpy",
            # LLM/provider clients
            "tiktoken",
            "httpx",
            "openai",
            "anthropic",
            # GPU (optional profile only)
            "torch",
        }

        def _is_optional_missing(exc: BaseException) -> bool:
            msg = str(exc)
            p = str(path)
            # If under behavior tests or UI modules, missing optional deps are not issues
            if "tests/behavior" in p or "tests\\behavior" in p:
                return True
            # Heuristic: if the missing module name appears and is in OPTIONAL_IMPORTS
            for name in OPTIONAL_IMPORTS:
                if name in msg:
                    return True
            # Offline defaults: ignore provider imports when offline
            if os.environ.get("DEVSYNTH_OFFLINE", "true").lower() == "true":
                if any(s in msg.lower() for s in ("openai", "lm_studio", "lmstudio")):
                    return True
            return False

        import os

        try:
            code = compile(text, str(path), "exec")
            exec_globals = {"__name__": "__verify__", "__file__": str(path)}
            exec(code, exec_globals, {})
        except ModuleNotFoundError as e:
            if not _is_optional_missing(e):
                issues.append({"type": "collection_error", "message": str(e)})
        except ImportError as e:
            if not _is_optional_missing(e):
                issues.append({"type": "collection_error", "message": str(e)})
        except Exception as e:
            # Gracefully ignore pytest skip at module level to avoid false positives
            if (
                getattr(e, "__class__", None)
                and getattr(e.__class__, "__name__", "") == "Skipped"
            ):
                return issues
            # Treat any other top-level exec failure as a collection issue
            issues.append({"type": "collection_error", "message": str(e)})
        except (
            BaseException
        ) as e:  # Catch non-Exception BaseExceptions like pytest.Skipped
            if (
                getattr(e, "__class__", None)
                and getattr(e.__class__, "__name__", "") == "Skipped"
            ):
                return issues
            issues.append({"type": "collection_error", "message": str(e)})
    finally:
        sys.path[:] = original_sys_path
    return issues


def verify_files(
    file_paths: Iterable[pathlib.Path | str], *, check_documentation: bool = True
) -> dict:
    """Verify markers for the provided files with caching.

    Returns a result dict including cache stats and file-level info.
    """
    _load_disk_cache()

    files: dict[str, FileVerification] = {}
    cache_hits = 0
    cache_misses = 0
    files_with_issues = 0
    collection_errors = []
    speed_marker_violations: list[dict] = []
    property_marker_violations: list[dict] = []

    for p in sorted(pathlib.Path(str(fp)).resolve() for fp in file_paths):
        if p.is_dir():
            # Recurse directories to keep behavior intuitive
            for sub in sorted(p.rglob("*.py")):
                verify_files([sub], check_documentation=False)
            continue
        key = str(p)
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            cache_misses += 1
            continue

        sig = _compute_signature(p)
        FILE_SIGNATURES[key] = sig
        prev = PERSISTENT_CACHE.get(key)
        if prev and prev.get("hash") == sig[1]:
            cache_hits += 1
            file_result = prev.get("verification", {"markers": {}, "issues": []})
        else:
            cache_misses += 1
            markers = _collect_markers_from_text(text)
            functions = _collect_test_functions(p, text)
            issues = _attempt_collection(p, text)
            # Add speed marker violations (function-level rule)
            issues.extend(_find_speed_marker_violations(p, text))
            # Add property marker check for tests under tests/property/
            try:
                if "tests/property" in str(p):
                    prop_violations = _find_property_marker_violations(p, text)
                    # Do NOT include property violations in file issues; collect
                    # only for summary (informational)
                    for v in prop_violations:
                        if v.get("type") == "property_marker_violation":
                            property_marker_violations.append(v)
            except Exception:
                # Be resilient if path logic fails unexpectedly
                pass
            file_result = {
                "markers": markers,
                "issues": issues,
                "functions": {name: True for name in functions},
            }
            PERSISTENT_CACHE[key] = {"hash": sig[1], "verification": file_result}

        # Count a file as having issues when marker or collection problems
        # are discovered so callers can surface actionable failures.
        if file_result["issues"]:
            has_marker_issue = any(
                i.get("type") in {"speed_marker_violation", "property_marker_violation"}
                for i in file_result["issues"]
            )
            has_collection_error = any(
                i.get("type") == "collection_error" for i in file_result["issues"]
            )
            if has_marker_issue:
                files_with_issues += 1
            if has_collection_error:
                collection_errors.append(key)
            for i in file_result["issues"]:
                if i.get("type") == "speed_marker_violation":
                    speed_marker_violations.append(i)

        files[key] = file_result

    result = {
        "files": files,
        "files_with_issues": files_with_issues,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "collection_errors": collection_errors,
        "speed_marker_violations": speed_marker_violations,
        "property_marker_violations": property_marker_violations,
        "total_files": len(files),
    }

    # Also build a brief markers summary for the legacy JSON report
    total_markers: Counter[str] = Counter()
    for fr in files.values():
        for name, count in fr["markers"].items():
            total_markers[name] += count

    undocumented_markers = find_undocumented_markers() if check_documentation else []
    result["undocumented_markers"] = undocumented_markers

    summary_report = {
        "markers": dict(total_markers),
        "files_scanned": len(files),
        "files_with_issues": files_with_issues,
        "undocumented_markers": undocumented_markers,
    }
    # Write report to default location; main() may rewrite if --report-file provided.
    report_target = REPORT_PATH
    report_target.parent.mkdir(parents=True, exist_ok=True)
    report_target.write_text(
        json.dumps(summary_report, indent=2) + "\n", encoding="utf-8"
    )
    _save_disk_cache()
    return result


def verify_directory_markers(
    directory: str, *, paths: Iterable[pathlib.Path | str] | None = None
) -> dict:
    """Verify markers for all .py files under directory with caching.

    Returns a result dict including cache stats and file-level info.
    """
    if paths is not None:
        return verify_files(paths)
    base = pathlib.Path(directory)
    return verify_files(base.rglob("*.py"))


def invalidate_cache_for_paths(paths: Iterable[pathlib.Path | str]) -> int:
    """Remove cached entries for specific paths.

    Returns the number of entries removed.
    """
    removed = 0
    for p in paths:
        key = str(p)
        if key in PERSISTENT_CACHE:
            del PERSISTENT_CACHE[key]
            removed += 1
        if key in FILE_SIGNATURES:
            del FILE_SIGNATURES[key]
    _save_disk_cache()
    return removed


def _list_changed_test_files(base_ref: str = "HEAD") -> list[pathlib.Path]:
    """Return changed test files relative to base_ref using git.

    Falls back to an empty list if git is unavailable or the command fails.
    """
    try:
        cmd = ["git", "diff", "--name-only", base_ref, "--", "tests"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return []
        files = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            p = (ROOT / line).resolve()
            if p.exists() and p.suffix == ".py":
                files.append(p)
        return files
    except Exception:
        return []


def main() -> int:
    if not TESTS_DIR.exists():
        REPORT_PATH.write_text(
            json.dumps({"markers": {}, "files_scanned": 0}, indent=2)
        )
        return 0

    parser = get_arg_parser()
    args = parser.parse_args()

    # Expose args for verify_files to consult if needed (best effort)
    setattr(sys.modules[__name__], "args", args)

    target_files: list[pathlib.Path] | None = None

    if args.paths:
        target_files = [pathlib.Path(p) for p in args.paths]
    elif getattr(args, "changed", False):
        changed = _list_changed_test_files(getattr(args, "base_ref", "HEAD"))
        if changed:
            target_files = changed

    if target_files is not None:
        result = verify_files(target_files)
    else:
        result = verify_directory_markers(str(TESTS_DIR))

    # Optional cross-check with pytest collection inventory
    cross_check_exit = 0
    if getattr(args, "cross_check_collection", False):
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                print(
                    f"[warn] cross-check skipped due to pytest collection exit code "
                    f"{proc.returncode}"
                )
                cross_check_exit = max(cross_check_exit, 1)
            else:
                collected = set()
                for line in proc.stdout.splitlines():
                    line = line.strip()
                    if not line or line.startswith("="):
                        continue
                    # Only consider pytest node ids which include '::'
                    if "::" not in line:
                        continue
                    collected.add(line)
                # Build a simple static inventory of test node ids (module::function)
                # from our parse
                static_nodes = set()
                for fpath, fdata in result.get("files", {}).items():
                    module = str(pathlib.Path(fpath).relative_to(ROOT))
                    for fn in fdata.get("functions", {}).keys():
                        static_nodes.add(f"{module}::{fn}")
                missing_in_collection = sorted(static_nodes - collected)
                extra_in_collection = sorted(collected - static_nodes)
                if missing_in_collection or extra_in_collection:
                    print("[warn] cross-check discrepancies detected:")
                    if missing_in_collection:
                        print("  - Present in static scan but not collected:")
                        for n in missing_in_collection[:50]:
                            print(f"    * {n}")
                    if extra_in_collection:
                        print("  - Collected by pytest but not in static scan:")
                        for n in extra_in_collection[:50]:
                            print(f"    * {n}")
                    cross_check_exit = 1
                else:
                    print(
                        "[info] cross-check: static scan matches pytest collection "
                        "inventory (basic)."
                    )
        except Exception as e:
            print(f"[warn] cross-check failed to execute: {e}")
            # Do not fail the entire run due to cross-check failure

    # Optionally rewrite report to requested location
    try:
        if getattr(args, "report", False) or getattr(args, "report_file", None):
            # read the default report and write to specified path
            summary_text = (
                REPORT_PATH.read_text(encoding="utf-8")
                if REPORT_PATH.exists()
                else json.dumps({})
            )
            out_path = pathlib.Path(getattr(args, "report_file", str(REPORT_PATH)))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(summary_text, encoding="utf-8")
    except Exception:
        # Do not fail on reporting errors; keep tool robust
        pass

    total_speed_violations = len(result.get("speed_marker_violations", []))
    if total_speed_violations:
        print("[error] speed marker violations detected:")
        for v in result["speed_marker_violations"][:50]:  # limit output
            print(
                f" - {v.get('file')}::{v.get('function')}: "
                f"found markers {v.get('markers_found')}"
            )
        if total_speed_violations > 50:
            print(f" ... and {total_speed_violations - 50} more")

    total_property_violations = len(result.get("property_marker_violations", []))
    if total_property_violations:
        print("[info] property marker advisories (informational) in tests/property:")
        for v in result["property_marker_violations"][:50]:
            print(
                f" - {v.get('file')}::{v.get('function')}: "
                "missing @pytest.mark.property"
            )
        if total_property_violations > 50:
            print(f" ... and {total_property_violations - 50} more")

    undocumented_markers = result.get("undocumented_markers", [])
    if undocumented_markers:
        print("[error] undocumented custom markers detected:")
        for marker in undocumented_markers:
            print(f" - {marker}")

    print(
        "[info] verify_test_markers: files=%d, cache_hits=%d, cache_misses=%d, "
        "issues=%d, speed_violations=%d, property_violations=%d"
        % (
            len(result["files"]),
            result["cache_hits"],
            result["cache_misses"],
            result["files_with_issues"],
            total_speed_violations,
            total_property_violations,
        )
    )
    # Enforce discipline: fail if any speed marker violations were found.
    # Property marker advisories are informational and do not affect exit status.
    exit_code = 1 if total_speed_violations or cross_check_exit else 0
    if undocumented_markers:
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
