#!/usr/bin/env python3
"""
Commit repository changes in logical chunks, sequentially, using a best-practices approach.

Features
- Groups changes by domain: ci, docs, src, tests (unit/integration/behavior/examples), scripts, config, misc.
- Default is dry-run; requires --execute to actually commit.
- Conventional Commit messages with optional Socratic/Dialectical reasoning footer (--socratic).
- Can filter which groups to include, and whether to include untracked files.

Usage examples
- Dry run (plan only):
    python scripts/commit_logical_chunks.py
- Execute with reasoning footer:
    python scripts/commit_logical_chunks.py --execute --socratic
- Only commit tests and src groups:
    python scripts/commit_logical_chunks.py --execute --groups tests src

Notes
- This script avoids third-party deps; uses subprocess and argparse.
- It respects .gitignore; untracked files are excluded unless --include-untracked is passed.
- It commits only files detected by `git status --porcelain=v1`.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
from collections.abc import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

StatusLine = tuple[str, str]  # (status_code, path)


def run(
    cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def git_status_porcelain(include_untracked: bool) -> list[StatusLine]:
    # --untracked-files=no to exclude untracked; default is normal
    args = ["git", "status", "--porcelain=v1"]
    if not include_untracked:
        args.append("--untracked-files=no")
    cp = run(args)
    if cp.returncode != 0:
        raise RuntimeError(f"git status failed: {cp.stderr.strip()}")
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    results: list[StatusLine] = []
    # Format: XY <path> (rename shows 'R  old -> new')
    for ln in lines:
        status = ln[:2].strip()
        rest = ln[3:]
        # handle rename as path after '->'
        if "->" in rest:
            path = rest.split("->", 1)[1].strip()
        else:
            path = rest.strip()
        results.append((status, path))
    return results


@dataclass
class Group:
    name: str
    description: str
    matcher: re.Pattern[str]
    conventional_type: str
    paths: list[str] = field(default_factory=list)


def build_groups() -> list[Group]:
    # Define matchers for groups. First match wins; order matters.
    patterns: list[Group] = [
        Group(
            name="ci",
            description="CI workflows and automation",
            matcher=re.compile(r"^\.github/"),
            conventional_type="ci",
        ),
        Group(
            name="docs",
            description="Documentation and guides",
            matcher=re.compile(
                r"^(docs/|README\.md$|CHANGELOG\.md$|AGENTS\.md$|mkdocs\.yml$)"
            ),
            conventional_type="docs",
        ),
        Group(
            name="src",
            description="Source code under src/",
            matcher=re.compile(r"^src/"),
            conventional_type="feat",  # may be overridden per commit message if desired
        ),
        Group(
            name="tests-unit",
            description="Unit tests",
            matcher=re.compile(r"^tests/unit/"),
            conventional_type="test",
        ),
        Group(
            name="tests-integration",
            description="Integration tests",
            matcher=re.compile(r"^tests/integration/"),
            conventional_type="test",
        ),
        Group(
            name="tests-behavior",
            description="Behavior tests",
            matcher=re.compile(r"^tests/behavior/"),
            conventional_type="test",
        ),
        Group(
            name="tests-examples",
            description="Example tests",
            matcher=re.compile(r"^tests/examples/"),
            conventional_type="test",
        ),
        Group(
            name="scripts",
            description="Repository scripts",
            matcher=re.compile(r"^scripts/"),
            conventional_type="chore",
        ),
        Group(
            name="config",
            description="Build and project configuration",
            matcher=re.compile(
                r"^(pyproject\.toml$|poetry\.toml$|poetry\.lock$|pytest\.ini$|Taskfile\.yml$|Dockerfile$|docker-compose.*\.yml$|deployment/|config/|templates/)"
            ),
            conventional_type="build",
        ),
        Group(
            name="misc",
            description="Miscellaneous top-level files",
            matcher=re.compile(r"^[^/]+$"),  # files in repo root not matched earlier
            conventional_type="chore",
        ),
    ]
    return patterns


def assign_to_groups(status: list[StatusLine], groups: list[Group]) -> dict[str, Group]:
    by_name: dict[str, Group] = {g.name: g for g in groups}
    for _, path in status:
        # Skip internal cache directories created by tests/tools
        if (
            path.startswith(".pytest_cache/")
            or path.startswith(".mypy_cache/")
            or path.startswith(".test_collection_cache/")
        ):
            continue
        matched = False
        for g in groups:
            if g.matcher.search(path):
                g.paths.append(path)
                matched = True
                break
        if not matched:
            by_name["misc"].paths.append(path)
    return by_name


def build_commit_message(group: Group, socratic: bool) -> str:
    scope = group.name
    header = f"{group.conventional_type}({scope}): update {group.description}"
    if not socratic:
        return header
    # Provide a concise dialectical footer
    socratic_footer = (
        "\n\n"
        "Socratic-Questions: What is the minimal, coherent unit of change here? What risks arise if mixed?\n"
        "Dialectic: Thesis—group related files for clarity; Antithesis—large single commit for speed; "
        "Synthesis—sequential logical commits improving traceability with low overhead.\n"
    )
    return header + socratic_footer


def _git_identity_env() -> dict[str, str]:
    """Return environment variables to ensure git has an identity and no signing.

    If the user already has GIT_* env vars set, we do not override them.
    """
    env: dict[str, str] = {}
    defaults = {
        "GIT_AUTHOR_NAME": "DevSynth Commit Bot",
        "GIT_AUTHOR_EMAIL": "commitbot@example.com",
        "GIT_COMMITTER_NAME": "DevSynth Commit Bot",
        "GIT_COMMITTER_EMAIL": "commitbot@example.com",
        # Avoid GPG signing failures in ephemeral environments
        "GIT_TRACE": os.environ.get("GIT_TRACE", "0"),
    }
    for k, v in defaults.items():
        if k not in os.environ:
            env[k] = v
    return env


def stage_and_commit(paths: Iterable[str], message: str, execute: bool) -> None:
    if not paths:
        return
    if execute:
        env = _git_identity_env()
        add_cp = run(["git", "add", "--"] + list(paths), env=env)
        if add_cp.returncode != 0:
            raise RuntimeError(
                f"git add failed:\nSTDERR: {add_cp.stderr}\nSTDOUT: {add_cp.stdout}"
            )
        commit_cp = run(["git", "commit", "--no-gpg-sign", "-m", message], env=env)
        if commit_cp.returncode != 0:
            raise RuntimeError(
                "git commit failed:\n"
                f"STDERR: {commit_cp.stderr}\nSTDOUT: {commit_cp.stdout}"
            )
        else:
            print(
                "[executed] Committed group with message header: "
                + message.split("\n", 1)[0]
            )
    else:
        print("[dry-run] Would stage and commit:")
        for p in paths:
            print(f"  - {p}")
        print("[dry-run] Commit message:\n" + message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="Perform commits; default is dry-run"
    )
    parser.add_argument(
        "--socratic",
        action="store_true",
        help="Include Socratic/Dialectical reasoning in commit messages",
    )
    parser.add_argument(
        "--groups",
        nargs="*",
        default=None,
        help="Restrict to specific group names (e.g., ci docs src tests-unit)",
    )
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="Include untracked files (respects .gitignore)",
    )
    args = parser.parse_args()

    status = git_status_porcelain(include_untracked=args.include_untracked)
    if not status:
        print("No changes detected. Exiting.")
        return

    groups = build_groups()
    grouped = assign_to_groups(status, groups)

    # Execution order: ci -> config -> src -> tests (unit, integration, behavior, examples) -> scripts -> docs -> misc
    order = [
        "ci",
        "config",
        "src",
        "tests-unit",
        "tests-integration",
        "tests-behavior",
        "tests-examples",
        "scripts",
        "docs",
        "misc",
    ]

    # Validate filter
    filter_set = set(args.groups) if args.groups else None
    unknown_filters = (
        set() if not filter_set else {g for g in filter_set if g not in grouped}
    )
    if unknown_filters:
        print("Unknown group names:", ", ".join(sorted(unknown_filters)))
        print("Known groups:", ", ".join(sorted(grouped.keys())))
        raise SystemExit(2)

    planned_total = 0
    for name in order:
        if filter_set and name not in filter_set:
            continue
        group = grouped[name]
        if not group.paths:
            continue
        planned_total += 1
        msg = build_commit_message(group, args.socratic)
        print(f"\n== Group: {name} ({len(group.paths)} files) ==")
        stage_and_commit(group.paths, msg, execute=args.execute)

    if planned_total == 0:
        print("No matching changes for the selected groups.")
    else:
        print("\nDone.")


if __name__ == "__main__":
    main()
