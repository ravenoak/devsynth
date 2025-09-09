"""Implement 'devsynth vcs fix-rebase-pr' command.

Purpose
-------
When a branch (e.g., 'release-prep') has been rebased and force-pushed, GitHub
may refuse a "Rebase and merge" on the PR due to conflicts or non-linear
history constraints. This utility safely reconstructs a new branch based on the
latest base (e.g., 'main') and cherry-picks the unique commits from the source
branch in order. This avoids losing work and produces a mergeable PR.

Design notes
------------
- Default source branch: 'release-prep'
- Default base branch: 'main'
- Creates a new local branch from base, cherry-picks commits unique to source.
- Dry-run by default; requires --execute to perform changes.
- Optional --push to push the new branch to a remote.
- Uses only subprocess calls to git; no external dependencies.
- Outputs clear, dialectical guidance via UXBridge without adding docs.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


@dataclass
class FixPlan:
    base_branch: str
    source_branch: str
    new_branch: str
    remote: str
    commits: list[str]


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _call_git(args: Sequence[str]) -> None:
    subprocess.check_call(["git", *args])


def _ensure_clean_worktree() -> None:
    status = _run_git(["status", "--porcelain"])  # empty => clean
    if status:
        raise RuntimeError(
            "Working tree not clean. Commit/stash changes before running this command."
        )


def _fetch(remote: str) -> None:
    _call_git(["fetch", remote, "--prune"])


def _branch_exists(ref: str) -> bool:
    try:
        _run_git(["rev-parse", "--verify", ref])
        return True
    except subprocess.CalledProcessError:
        return False


def _list_unique_commits(source_ref: str, base_ref: str) -> list[str]:
    # List commits reachable from source but not from base.
    # Topological order oldest..newest ensures safe cherry-picking.
    out = _run_git(["rev-list", "--reverse", f"{base_ref}..{source_ref}"])
    commits = [c for c in out.splitlines() if c]
    return commits


def _current_branch() -> str:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def _create_branch(base_ref: str, new_branch: str) -> None:
    _call_git(["switch", "-c", new_branch, base_ref])


def _cherry_pick(commits: Sequence[str]) -> None:
    for c in commits:
        _call_git(["cherry-pick", "-x", c])


def _push(remote: str, branch: str, set_upstream: bool = True) -> None:
    args = ["push", remote, branch]
    if set_upstream:
        args.insert(1, "-u")
    _call_git(args)


def _plan_fix(
    *,
    base_branch: str,
    source_branch: str,
    remote: str,
    new_branch: str | None,
) -> FixPlan:
    # Compute default new branch name if not provided
    if not new_branch:
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        new_branch = f"{source_branch}-fix-{stamp}"

    base_ref = f"{remote}/{base_branch}"
    source_ref = f"{remote}/{source_branch}"

    commits = _list_unique_commits(source_ref, base_ref)
    return FixPlan(
        base_branch=base_branch,
        source_branch=source_branch,
        new_branch=new_branch,
        remote=remote,
        commits=commits,
    )


def fix_rebase_pr_cmd(
    *,
    base_branch: str = "main",
    source_branch: str = "release-prep",
    remote: str = "origin",
    new_branch: str | None = None,
    execute: bool = False,
    push: bool = False,
    bridge: UXBridge | None = None,
) -> None:
    """Recreate a mergeable PR branch by cherry-picking unique commits onto base.

    Args:
        base_branch: Base branch name (typically 'main').
        source_branch: The feature/release branch to salvage (e.g., 'release-prep').
        remote: Git remote name (default 'origin').
        new_branch: Optional name for the new branch. Defaults to '<source>-fix-<ts>'.
        execute: Perform actions; if False, show a dry-run plan only.
        push: If executing, also push the new branch to the remote and set upstream.
        bridge: UX bridge for user interaction.

    Behavior:
        - Validates clean working tree.
        - Fetches remote.
        - Builds the commit list unique to source vs base.
        - Shows a plan with dialectical notes for safety and reversibility.
        - If --execute: creates branch from base and cherry-picks commits in order.
        - Optionally pushes the branch and outputs next-step instructions.
    """
    ux = bridge or CLIUXBridge()

    try:
        _ensure_clean_worktree()
    except Exception as e:
        ux.display_error(str(e))
        return

    # Ensure remote refs are up-to-date
    try:
        _fetch(remote)
    except subprocess.CalledProcessError as e:
        ux.display_error(f"Failed to fetch from remote '{remote}': {e}")
        return

    try:
        plan = _plan_fix(
            base_branch=base_branch,
            source_branch=source_branch,
            remote=remote,
            new_branch=new_branch,
        )
    except subprocess.CalledProcessError as e:
        ux.display_error(
            "Failed to compute commit plan. Ensure branches exist on the remote. "
            f"Details: {e}"
        )
        return

    if not plan.commits:
        ux.display_result(
            "Source branch has no unique commits relative to base; nothing to "
            "cherry-pick.\nIf GitHub blocks rebase-merge, consider using "
            "'Squash and merge' or re-opening PR."
        )
        return

    lines: list[str] = []
    lines.append("Fix plan (dry-run by default):")
    lines.append(f"- Remote: {plan.remote}")
    lines.append(f"- Base:   {plan.remote}/{plan.base_branch}")
    lines.append(f"- Source: {plan.remote}/{plan.source_branch}")
    lines.append(f"- New branch to create: {plan.new_branch}")
    lines.append(f"- Commits to cherry-pick (oldest→newest): {len(plan.commits)}")
    sample = ", ".join(plan.commits[:5]) + ("…" if len(plan.commits) > 5 else "")
    lines.append(f"  {sample}")
    lines.append("")
    lines.append(
        "Dialectical safety: This approach preserves each commit's intent while "
        "constructing a linear branch off base."
    )
    lines.append(
        "Socratic check: If a cherry-pick fails due to conflicts, you can resolve "
        "and continue, or abort to keep repo intact."
    )

    ux.display_result("\n".join(lines))

    if not execute:
        ux.display_result(
            "Dry-run only. Re-run with --execute to create the branch and "
            "cherry-pick commits."
        )
        return

    current = _current_branch()
    try:
        # Ensure the new branch name doesn't already exist locally
        if _branch_exists(plan.new_branch):
            raise RuntimeError(
                f"Local branch '{plan.new_branch}' already exists. "
                "Choose a different --new-branch name."
            )

        # Create new branch from base
        _create_branch(f"{plan.remote}/{plan.base_branch}", plan.new_branch)
        # Cherry-pick commits oldest to newest
        _cherry_pick(plan.commits)

        if push:
            _push(plan.remote, plan.new_branch, set_upstream=True)

    except subprocess.CalledProcessError as e:
        ux.display_error(
            "A git command failed during execution. You can inspect the "
            "repository state and run:\n"
            "  git cherry-pick --abort  # if a cherry-pick is in progress\n"
            f"  git switch {current}\n"
            f"Details: {e}"
        )
        return
    except Exception as e:
        ux.display_error(str(e))
        return
    finally:
        # Do not auto-switch back; we leave the user on the new branch intentionally.
        pass

    next_steps: list[str] = [
        "Fix applied successfully.",
        f"Current branch: {plan.new_branch}",
    ]
    if push:
        next_steps.append(
            f"Branch pushed to {plan.remote}/{plan.new_branch}. "
            f"Open a PR targeting {plan.base_branch}."
        )
    else:
        next_steps.extend(
            [
                "Push the branch and open a PR:",
                f"  git push -u {plan.remote} {plan.new_branch}",
                f"  # then open a PR into {plan.base_branch}",
            ]
        )

    ux.display_result("\n".join(next_steps))


__all__ = ["fix_rebase_pr_cmd"]
