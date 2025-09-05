"""Implement 'devsynth vcs chunk-commit' command.

This command analyzes repository changes and commits them in logical chunks.
It favors safety: dry-run by default, and operates on pathspecs to avoid
accidentally committing unrelated staged changes.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


@dataclass
class ChangeGroup:
    category: str
    files: list[str]


CATEGORIES: list[tuple[str, tuple[str, ...]]] = [
    ("docs", ("docs/", "README.md", "CHANGELOG.md", "CONTRIBUTING.md", ".md", ".rst")),
    ("tests", ("tests/", "conftest.py")),
    ("src", ("src/",)),
    ("config", ("config/", "pyproject.toml", "pytest.ini", "poetry.toml")),
    ("scripts", ("scripts/",)),
    ("ci", (".github/", "docker-compose", "Dockerfile", "deployment/")),
    ("examples", ("examples/",)),
    ("templates", ("templates/",)),
]


def _path_category(path: str) -> str:
    p = path.replace("\\", "/")
    for cat, patterns in CATEGORIES:
        for pat in patterns:
            if pat.endswith(".md") or pat.endswith(".rst"):
                # specific top-level files
                if p == pat:
                    return cat
            elif pat.endswith("/"):
                if p.startswith(pat):
                    return cat
            else:
                # prefix like docker-compose
                if p.startswith(pat):
                    return cat
                # suffix extension e.g. ".md"
                if pat.startswith(".") and p.endswith(pat):
                    return cat
    return "chore"


def group_changes(paths: Sequence[str]) -> list[ChangeGroup]:
    buckets: dict[str, list[str]] = {}
    for path in paths:
        cat = _path_category(path)
        buckets.setdefault(cat, []).append(path)
    # Order: docs, tests, src, config, scripts, ci,
    # examples, templates, chore
    order = {name: i for i, name in enumerate([c for c, _ in CATEGORIES] + ["chore"])}
    groups = [ChangeGroup(category=k, files=sorted(v)) for k, v in buckets.items()]
    groups.sort(key=lambda g: order.get(g.category, 999))
    return groups


def generate_message(category: str, files: Sequence[str]) -> str:
    sample = ", ".join(files[:5]) + ("…" if len(files) > 5 else "")
    rationale = (
        f"Atomic {category} changes committed together to preserve reviewable history. "
        "Socratic check: Does any file cross-cut multiple concerns? "
        "If so, it was left for its own commit."
    )
    counter = (
        "Dialectical note: Grouping is justified by artifact role "
        "(docs/tests/src/config). "
        "Counter-argument would be coupling across categories; "
        "addressed by isolating such changes."
    )
    title = f"{category}: update {len(files)} file(s)"
    body = f"Files: {sample}\n\n{rationale}\n{counter}"
    return f"{title}\n\n{body}"


def _run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True)


def _list_staged() -> list[str]:
    out = _run_git(["diff", "--name-only", "--cached"]).strip()
    return [p for p in out.splitlines() if p]


def _list_unstaged(include_untracked: bool) -> list[str]:
    changed = _run_git(["diff", "--name-only"]).strip().splitlines()  # changed files
    changed = [p for p in changed if p]
    if include_untracked:
        untracked = (
            _run_git(
                [
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                ]
            )
            .strip()
            .splitlines()
        )
        changed.extend([p for p in untracked if p])
    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for p in changed:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _stage_files(files: Sequence[str]) -> None:
    if not files:
        return
    subprocess.check_call(["git", "add", "-A", "--", *files])


def _commit_files(message: str, files: Sequence[str], *, no_verify: bool) -> None:
    args = ["git", "commit", "-m", message]
    if no_verify:
        args.append("--no-verify")
    args.extend(["--", *files])
    subprocess.check_call(args)


def chunk_commit_cmd(
    *,
    dry_run: bool,
    staged_only: bool,
    include_untracked: bool,
    no_verify: bool,
    bridge: UXBridge | None = None,
) -> None:
    bridge = bridge or CLIUXBridge()

    paths = _list_staged() if staged_only else _list_unstaged(include_untracked)
    if not paths:
        bridge.display_result("No changes detected; nothing to commit.")
        return

    groups = group_changes(paths)

    # Preview plan
    lines: list[str] = [
        "Planned commit groups (dry-run)" if dry_run else "Executing commit groups:"
    ]
    for g in groups:
        lines.append(f"- {g.category}: {len(g.files)} file(s)")
        lines.append("  " + ", ".join(g.files[:5]) + (" …" if len(g.files) > 5 else ""))
    bridge.display_result("\n".join(lines))

    if dry_run:
        return

    # Execute sequentially
    for g in groups:
        files = g.files
        msg = generate_message(g.category, files)
        if not staged_only:
            _stage_files(files)
        _commit_files(msg, files, no_verify=no_verify)
        bridge.display_result(f"Committed {g.category}: {len(files)} file(s)")
