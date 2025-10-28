#!/usr/bin/env python3
"""Ensure issue tickets link to specs and BDD features.

This utility scans ``issues/*.md`` (excluding ``README.md`` and ``TEMPLATE.md``)
and performs two maintenance actions:

* Removes spurious ``None`` entries from the ``Dependencies`` field.
* Populates the ``## References`` section with links to the corresponding
  specification and BDD feature.

The script derives the expected paths from the ticket filename. For example,
``devsynth-run-tests-command.md`` links to
``docs/specifications/devsynth-run-tests-command.md`` and
``tests/behavior/features/devsynth_run_tests_command.feature``.
"""
from __future__ import annotations

import pathlib
from typing import List

ISSUES_DIR = pathlib.Path("issues")
SPEC_DIR = pathlib.Path("docs/specifications")
FEATURE_DIR = pathlib.Path("tests/behavior/features")


def update_issue(path: pathlib.Path) -> bool:
    """Update ``path`` in-place. Return ``True`` if changes were made."""
    lines = path.read_text().splitlines()
    slug = path.stem.lower()
    spec_path = SPEC_DIR / f"{slug}.md"
    feature_path = FEATURE_DIR / f"{slug.replace('-', '_')}.feature"
    changed = False

    # --- Dependencies field -------------------------------------------------
    for i, line in enumerate(lines):
        if line.startswith("Dependencies:"):
            deps = [d.strip() for d in line.split(":", 1)[1].split(",")]
            deps = [d for d in deps if d and d.lower() != "none"]
            if str(spec_path) not in deps:
                deps.append(str(spec_path))
                changed = True
            if str(feature_path) not in deps:
                deps.append(str(feature_path))
                changed = True
            lines[i] = "Dependencies: " + ", ".join(deps)
            break

    # --- References section -------------------------------------------------
    ref_header = None
    for i, line in enumerate(lines):
        if line.strip() == "## References":
            ref_header = i
            break
    if ref_header is None:
        lines.append("## References")
        ref_header = len(lines) - 1
        lines.append("")
        changed = True
    j = ref_header + 1
    refs: list[str] = []
    while j < len(lines) and lines[j].startswith("-"):
        refs.append(lines[j].strip())
        j += 1
    refs = [r for r in refs if r != "- None"]
    spec_line = f"- Specification: {spec_path}"
    feature_line = f"- BDD Feature: {feature_path}"
    if spec_line not in refs:
        refs.append(spec_line)
        changed = True
    if feature_line not in refs:
        refs.append(feature_line)
        changed = True
    if not refs:
        refs = ["- None"]
    lines[ref_header + 1 : j] = refs

    if changed:
        path.write_text("\n".join(lines) + "\n")
    return changed


def main() -> None:
    modified = []
    for issue in sorted(ISSUES_DIR.glob("*.md")):
        if issue.name in {"README.md", "TEMPLATE.md"}:
            continue
        if update_issue(issue):
            modified.append(str(issue))
    if modified:
        print("Updated:")
        for m in modified:
            print(f" - {m}")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    main()
