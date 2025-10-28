#!/usr/bin/env python3
"""Update GitHub issues with links to commits.

This script scans a commit message for issue references and posts the commit URL
as a comment on each referenced issue. It helps keep GitHub issues in sync with
the commits that address them.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from typing import Set

import requests


def get_repo() -> str:
    """Return the ``owner/repo`` slug from the ``origin`` remote."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if result.startswith("git@"):
        path = result.split(":", 1)[1]
    elif result.startswith("https://") or result.startswith("http://"):
        path = result.split("github.com/", 1)[1]
    else:
        raise RuntimeError("Unsupported git remote URL format: %s" % result)

    if path.endswith(".git"):
        path = path[:-4]
    return path


def get_commit_message(commit: str) -> str:
    """Return the commit message for ``commit``."""
    return subprocess.run(
        ["git", "show", "--no-patch", "--format=%B", commit],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def extract_issue_numbers(message: str) -> set[int]:
    """Extract issue numbers from ``message`` in ``#123`` format."""
    return {int(num) for num in re.findall(r"#(\d+)", message)}


def comment_on_issue(
    repo: str, issue: int, commit_url: str, token: str, dry_run: bool
) -> None:
    """Post ``commit_url`` as a comment on ``issue`` if not already present."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments"

    if dry_run:
        print(f"Issue #{issue}: would comment with {commit_url}")
        return

    resp = requests.get(comments_url, headers=headers)
    resp.raise_for_status()
    if any(commit_url in c.get("body", "") for c in resp.json()):
        print(f"Issue #{issue}: link already exists, skipping")
        return

    body = {"body": f"Commit {commit_url} references this issue."}
    resp = requests.post(comments_url, headers=headers, json=body)
    resp.raise_for_status()
    print(f"Issue #{issue}: comment added")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add commit URL comments to referenced GitHub issues"
    )
    parser.add_argument(
        "--commit", default="HEAD", help="Commit hash to process (default: HEAD)"
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository in owner/repo format. Defaults to origin remote.",
    )
    parser.add_argument(
        "--token",
        help="GitHub token. Defaults to GITHUB_TOKEN or GH_TOKEN environment variables.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without posting to GitHub",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit(
            "A GitHub token is required. Set GITHUB_TOKEN or use --token to provide one."
        )

    repo = args.repo or get_repo()
    commit = subprocess.run(
        ["git", "rev-parse", args.commit],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    message = get_commit_message(commit)
    issues = extract_issue_numbers(message)

    if not issues:
        print("No issue references found in commit message")
        return

    commit_url = f"https://github.com/{repo}/commit/{commit}"
    for issue in sorted(issues):
        comment_on_issue(repo, issue, commit_url, token, args.dry_run)


if __name__ == "__main__":
    main()
