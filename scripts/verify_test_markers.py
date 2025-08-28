#!/usr/bin/env python3
"""Verify pytest markers and provide a cached, deterministic summary.

This script offers a lightweight verification surface to keep CI runs fast.
It scans test files for pytest markers, attempts a minimal 'collection' by
executing modules in an isolated namespace to catch basic import errors, and
uses a content-hash cache to avoid reprocessing unchanged files.

Adheres to .junie/guidelines.md: deterministic behavior, clear outputs, and
graceful failure handling. Designed to be extended along docs/plan.md.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
REPORT_PATH = ROOT / "test_markers_report.json"
CACHE_PATH = ROOT / ".cache" / "test_markers_cache.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

MARK_RE = re.compile(r"@pytest\.mark\.([a-zA-Z_][a-zA-Z0-9_]*)")

# In-memory caches (tests access these directly)
PERSISTENT_CACHE: Dict[str, dict] = {}
FILE_SIGNATURES: Dict[str, Tuple[float, str]] = {}


@dataclass
class FileVerification:
    markers: Dict[str, int]
    issues: list


def get_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Verify pytest markers with caching. By default scans the tests/ directory. "
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
        help="Path to write the JSON summary report (default: test_markers_report.json).",
    )
    return parser


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _compute_signature(path: pathlib.Path) -> Tuple[float, str]:
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


def _collect_markers_from_text(text: str) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for m in MARK_RE.finditer(text):
        counts[m.group(1)] += 1
    return dict(counts)


def _find_speed_marker_violations(path: pathlib.Path, text: str) -> List[dict]:
    """Return a list of violations for the exactly-one speed marker rule.

    Rules:
    - Prefer function-level decorators on test_ functions.
    - If no function-level speed marker is present, allow parametrize-level marks
      via pytest.param(..., marks=pytest.mark.<speed>) provided ALL parameters
      specify exactly the same single speed marker.
    - Allowed speed markers: fast | medium | slow.
    - Exactly one must be present overall; 0 or >1 are violations.
    - Module-level markers do not satisfy this requirement.
    """
    violations: List[dict] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        # Already handled elsewhere as a syntax error; skip here.
        return violations

    speed_markers = {"fast", "medium", "slow"}

    def _extract_marker_name_from_attr(a: ast.AST) -> Optional[str]:
        # Accept pytest.mark.<name> and pytest.mark.<name>()
        if isinstance(a, ast.Attribute):
            name = getattr(a, "attr", None)
            return name if isinstance(name, str) and name in speed_markers else None
        if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute):
            name = getattr(a.func, "attr", None)
            return name if isinstance(name, str) and name in speed_markers else None
        return None

    # Detect module-level speed markers assigned to pytestmark (disallowed)
    try:
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                # Handle: pytestmark = ... or: pytestmark: Any = ...
                target_names: List[str] = []
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
                    markers_found: List[str] = []
                    if isinstance(val, (ast.List, ast.Tuple)):
                        elements = list(getattr(val, "elts", []))
                    else:
                        elements = [val] if val is not None else []
                    for el in elements:
                        name = _extract_marker_name_from_attr(el)
                        if name:
                            markers_found.append(name)
                    if any(m in speed_markers for m in markers_found):
                        violations.append(
                            {
                                "type": "speed_marker_violation",
                                "function": "<module>",
                                "file": str(path),
                                "markers_found": markers_found,
                                "message": (
                                    "Module-level pytestmark with speed markers is not allowed; "
                                    "apply exactly one speed marker per test function."
                                ),
                            }
                        )
    except Exception:
        # Be permissive on AST shapes we don't anticipate
        pass

    def _collect_parametrize_speed_markers(dec: ast.Call) -> List[str]:
        """Inspect a @pytest.mark.parametrize decorator for pytest.param marks.

        We only consider markers embedded in pytest.param(..., marks=...). If every
        param has exactly one of {fast, medium, slow} and they are all identical,
        return that single marker; otherwise return [].
        """
        # Identify the argvalues argument: typically second positional arg
        argvalues: Optional[ast.AST] = None
        if dec.args:
            argvalues = dec.args[1] if len(dec.args) >= 2 else None
        for kw in getattr(dec, "keywords", []) or []:
            if getattr(kw, "arg", None) == "argvalues":
                argvalues = kw.value
                break
        if argvalues is None:
            return []
        # Normalize to a list of parameters
        elements: List[ast.AST] = []
        if isinstance(argvalues, (ast.List, ast.Tuple)):
            elements = list(argvalues.elts)
        else:
            # Not a static list/tuple; can't analyze safely
            return []
        all_param_markers: List[str] = []
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
                markers_here: List[str] = []
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

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Collect decorator names of the form pytest.mark.<name>
            found: List[str] = []
            parametrize_found: List[str] = []
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
            # Reconcile: prefer function-level marker; else consider parametrize-only
            effective = found or parametrize_found
            if len(effective) != 1:
                violations.append(
                    {
                        "type": "speed_marker_violation",
                        "function": node.name,
                        "file": str(path),
                        "markers_found": effective,
                        "message": (
                            f"Function {node.name} must have exactly one speed marker"
                        ),
                    }
                )
    return violations


def _attempt_collection(path: pathlib.Path, text: str) -> list:
    """Very light-weight 'collection' to catch obvious import errors.

    We parse to AST (to validate syntax) and then exec the module code in an
    isolated namespace to trigger import-time errors. We avoid running tests by
    not invoking pytest and by not calling any functions.
    """
    issues = []
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

    try:
        code = compile(text, str(path), "exec")
        exec_globals = {"__name__": "__verify__", "__file__": str(path)}
        exec(code, exec_globals, {})
    except ModuleNotFoundError as e:
        issues.append({"type": "collection_error", "message": str(e)})
    except ImportError as e:
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
    except BaseException as e:  # Catch non-Exception BaseExceptions like pytest.Skipped
        if (
            getattr(e, "__class__", None)
            and getattr(e.__class__, "__name__", "") == "Skipped"
        ):
            return issues
        issues.append({"type": "collection_error", "message": str(e)})
    return issues


def verify_files(file_paths: Iterable[pathlib.Path | str]) -> dict:
    """Verify markers for the provided files with caching.

    Returns a result dict including cache stats and file-level info.
    """
    _load_disk_cache()

    files: Dict[str, FileVerification] = {}
    cache_hits = 0
    cache_misses = 0
    files_with_issues = 0
    collection_errors = []
    speed_marker_violations: List[dict] = []

    for p in sorted(pathlib.Path(str(fp)).resolve() for fp in file_paths):
        if p.is_dir():
            # Recurse directories to keep behavior intuitive
            for sub in sorted(p.rglob("*.py")):
                # Re-enqueue sub files by tail recursion-like approach
                for _k, _v in verify_files([sub]).items():
                    # This branch is only used for side-effect updates, not ideal to merge dicts here
                    pass
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
            issues = _attempt_collection(p, text)
            # Add speed marker violations (function-level rule)
            issues.extend(_find_speed_marker_violations(p, text))
            file_result = {"markers": markers, "issues": issues}
            PERSISTENT_CACHE[key] = {"hash": sig[1], "verification": file_result}

        if file_result["issues"]:
            files_with_issues += 1
            if any(i.get("type") == "collection_error" for i in file_result["issues"]):
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
    }

    # Also build a brief markers summary for the legacy JSON report
    total_markers: Counter[str] = Counter()
    for fr in files.values():
        for name, count in fr["markers"].items():
            total_markers[name] += count

    summary_report = {
        "markers": dict(total_markers),
        "files_scanned": len(files),
        "files_with_issues": files_with_issues,
    }
    # Write report to requested location (legacy flag --report is accepted but optional)
    report_target = REPORT_PATH
    try:
        # Allow overriding report path via CLI
        arg_report_file = getattr(sys.modules.get("__main__"), "args", None)
    except Exception:
        arg_report_file = None
    # We cannot reliably access parsed args from here unless passed; we'll handle in main()
    # Default write to REPORT_PATH here; main() may also rewrite if --report-file provided.
    report_target.write_text(
        json.dumps(summary_report, indent=2) + "\n", encoding="utf-8"
    )
    _save_disk_cache()
    return result


def verify_directory_markers(directory: str) -> dict:
    """Verify markers for all .py files under directory with caching.

    Returns a result dict including cache stats and file-level info.
    """
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


def _list_changed_test_files(base_ref: str = "HEAD") -> List[pathlib.Path]:
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

    target_files: Optional[List[pathlib.Path]] = None

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
                f" - {v.get('file')}::{v.get('function')}: found markers {v.get('markers_found')}"
            )
        if total_speed_violations > 50:
            print(f" ... and {total_speed_violations - 50} more")

    print(
        "[info] verify_test_markers: files=%d, cache_hits=%d, cache_misses=%d, issues=%d, speed_violations=%d"
        % (
            len(result["files"]),
            result["cache_hits"],
            result["cache_misses"],
            result["files_with_issues"],
            total_speed_violations,
        )
    )
    # Enforce discipline: fail if any speed marker violations were found
    return 1 if total_speed_violations else 0


if __name__ == "__main__":
    sys.exit(main())
