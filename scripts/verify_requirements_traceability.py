#!/usr/bin/env python3
"""Validate requirements traceability matrix.

Ensures each requirement row includes references to code modules and tests.
"""

from __future__ import annotations

import argparse
import pathlib
import sys


def verify_traceability(matrix: pathlib.Path) -> int:
    """Return 0 if all requirements have code and test references."""
    errors = []
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
        "matrix", type=pathlib.Path, help="Path to requirements_traceability.md"
    )
    args = parser.parse_args()
    sys.exit(verify_traceability(args.matrix))


if __name__ == "__main__":
    main()
