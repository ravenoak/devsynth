#!/usr/bin/env python3
"""
Verify selected dependency constraints to avoid known breakages from transitive updates.

This script intentionally checks a small, high-risk subset that has caused issues in
many Python projects and in our stack:
- click: Typer 0.16 requires click >=8,<9
- anyio: httpx 0.28 requires anyio >=4,<5
- urllib3: requests 2.x requires urllib3 <3 (we also require >=2 for TLS fixes)

Exit code 0 on success; non-zero if constraints are violated. Prints actionable hints.

Usage:
  poetry run python scripts/verify_dependency_constraints.py

Design notes:
- Keep zero external deps; use importlib.metadata available in Python 3.12.
- Conservative ranges aligned to our current pyproject pins and lockfile.
- This complements Poetry pinning and offers a fast guard in CI.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from collections.abc import Callable, Iterable

try:
    from importlib.metadata import PackageNotFoundError, version
except Exception:  # pragma: no cover - Python <3.8 fallback not needed in CI
    from importlib_metadata import PackageNotFoundError, version  # type: ignore


@dataclass(frozen=True)
class Constraint:
    name: str
    checker: Callable[[str], bool]
    hint: str


def _parse_semver_tuple(v: str) -> tuple[int, int, int]:
    # Handle forms like "8.1.7" or "2.2" -> pad to 3 components
    parts = v.split(".")
    nums: list[int] = []
    for p in parts[:3]:
        n = 0
        i = 0
        while i < len(p) and p[i].isdigit():
            i += 1
        try:
            n = int(p[:i]) if i else 0
        except ValueError:
            n = 0
        nums.append(n)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)  # type: ignore[return-value]


def _range_check(
    v: str, lower_incl: tuple[int, int, int], upper_excl: tuple[int, int, int]
) -> bool:
    vt = _parse_semver_tuple(v)
    return (vt >= lower_incl) and (vt < upper_excl)


def main() -> int:
    constraints: Iterable[Constraint] = (
        Constraint(
            name="click",
            checker=lambda v: _range_check(v, (8, 0, 0), (9, 0, 0)),
            hint=(
                "Typer 0.16 requires click >=8,<9. Pin click to <9.0 if violated.\n"
                "See pyproject [tool.poetry.group.dev.dependencies]."
            ),
        ),
        Constraint(
            name="anyio",
            checker=lambda v: _range_check(v, (4, 0, 0), (5, 0, 0)),
            hint=("httpx 0.28 requires anyio >=4,<5. Pin anyio to <5.0 if violated."),
        ),
        Constraint(
            name="urllib3",
            checker=lambda v: _range_check(v, (2, 0, 0), (3, 0, 0)),
            hint=(
                "requests 2.x requires urllib3 <3. Ensure urllib3 stays on major 2.x."
            ),
        ),
    )

    failed: list[str] = []

    for c in constraints:
        try:
            v = version(c.name)
        except PackageNotFoundError:
            # Not installed in this profile; skip.
            continue
        ok = c.checker(v)
        if not ok:
            failed.append(f"{c.name}=={v}\n  -> {c.hint}")

    if failed:
        print("Dependency constraint violations detected:\n" + "\n".join(failed))
        return 2

    print(
        "Dependency constraints check passed: key transitive ranges are within policy."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
