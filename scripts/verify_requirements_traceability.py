#!/usr/bin/env python3
"""Validate requirements traceability matrix.

Ensures each requirement row includes references to code modules and tests.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def verify_traceability(matrix: pathlib.Path, spec_dir: pathlib.Path) -> int:
    """Return 0 if requirements and specs have code and test references."""
    errors: list[str] = []
    for lineno, line in enumerate(matrix.read_text().splitlines(), start=1):
        if (
            not line.startswith("| FR")
            and not line.startswith("| NFR")
            and not line.startswith("| IR")
        ):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 6:
            continue
        req_id, _, _, code_cell, test_cell, _ = parts
        if not code_cell or code_cell.lower() == "n/a":
            errors.append(f"{req_id} missing code reference (line {lineno})")
        if not test_cell or test_cell.lower() == "n/a":
            errors.append(f"{req_id} missing test reference (line {lineno})")
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
        has_code = "src/" in text
        has_test = "tests/" in text
        if not has_code:
            errors.append(
                f"{spec.relative_to(pathlib.Path('.'))} missing code reference"
            )
        if not has_test:
            errors.append(
                f"{spec.relative_to(pathlib.Path('.'))} missing test reference"
            )

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify requirements traceability matrix"
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
    args = parser.parse_args()
    sys.exit(verify_traceability(args.matrix, args.spec_dir))


if __name__ == "__main__":
    main()
