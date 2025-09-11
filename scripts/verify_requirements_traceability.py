#!/usr/bin/env python3
"""Validate requirements traceability matrix.

Ensures each requirement row includes references to code modules and tests and
that published specifications link to existing BDD feature files.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def verify_traceability(
    matrix: pathlib.Path, spec_dir: pathlib.Path
) -> tuple[list[str], int, int]:
    """Collect traceability errors and counts for requirements and specs."""
    errors: list[str] = []
    req_count = 0
    for lineno, line in enumerate(matrix.read_text().splitlines(), start=1):
        if (
            not line.startswith("| FR")
            and not line.startswith("| NFR")
            and not line.startswith("| IR")
        ):
            continue
        req_count += 1
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 6:
            continue
        req_id, _, _, code_cell, test_cell, _ = parts
        if not code_cell or code_cell.lower() == "n/a":
            errors.append(f"{req_id} missing code reference (line {lineno})")
        if not test_cell or test_cell.lower() == "n/a":
            errors.append(f"{req_id} missing test reference (line {lineno})")
    spec_count = 0
    for spec in spec_dir.glob("*.md"):
        if spec.name in {"index.md", "spec_template.md"}:
            continue
        text = spec.read_text()
        status = ""
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                front_matter = text[3:end]
                match = re.search(r"^status:\s*(\w+)", front_matter, re.MULTILINE)
                if match:
                    status = match.group(1).lower()
        if status != "published":
            continue
        spec_count += 1
        has_code = "src/" in text
        has_test = "tests/" in text
        feature_refs = set(
            re.findall(
                r"(?:\./|\.\./)*tests/behavior/features/[\w./-]+\.feature",
                text,
            )
        )
        if not has_code:
            errors.append(
                f"{spec.relative_to(pathlib.Path('.'))} missing code reference",
            )
        if not has_test:
            errors.append(
                f"{spec.relative_to(pathlib.Path('.'))} missing test reference",
            )
        if not feature_refs:
            errors.append(
                f"{spec.relative_to(pathlib.Path('.'))} missing BDD feature reference",
            )
        else:
            repo_root = pathlib.Path(".").resolve()
            spec_rel = spec.relative_to(pathlib.Path("."))
            for ref in feature_refs:
                ref_path = pathlib.Path(ref)
                if ref.startswith("tests/"):
                    feature_path = (repo_root / ref_path).resolve()
                else:
                    feature_path = (spec.parent / ref_path).resolve()
                if not feature_path.is_file():
                    missing_feature = feature_path.relative_to(repo_root)
                    errors.append(
                        f"{spec_rel} references missing feature {missing_feature}",
                    )
    return errors, req_count, spec_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify requirements traceability matrix",
    )
    parser.add_argument(
        "matrix",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path("docs/requirements_traceability.md"),
        help="Path to requirements_traceability.md",
    )
    parser.add_argument(
        "--spec-dir",
        type=pathlib.Path,
        default=pathlib.Path("docs/specifications"),
        help="Directory containing specification docs",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print errors",
    )
    args = parser.parse_args()
    errors, req_count, spec_count = verify_traceability(args.matrix, args.spec_dir)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        if not args.quiet:
            print(
                "Traceability check failed: "
                f"{len(errors)} issues found across {req_count} requirements "
                f"and {spec_count} published specs.",
                file=sys.stdout,
            )
        sys.exit(1)
    if not args.quiet:
        print(
            f"Verified {req_count} requirements and {spec_count} published "
            "specs; all traceability references present.",
            file=sys.stdout,
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
