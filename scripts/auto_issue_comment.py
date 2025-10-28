#!/usr/bin/env python3
"""Automatic issue comment/update mechanism.

This script annotates GitHub issues referenced by the latest commit message.
It is designed to be safe-by-default:
- If GITHUB_TOKEN or GITHUB_REPOSITORY are missing, it runs in dry-run mode.
- It handles GitHub API rate limits gracefully and exits zero on soft failures
  to avoid blocking CI in offline environments.

Usage:
  python scripts/auto_issue_comment.py [--commit <sha>] [--message <text>] [--dry-run]

Environment variables:
  GITHUB_TOKEN        Personal access token or workflow token (optional)
  GITHUB_REPOSITORY   "owner/repo" (optional)
  GITHUB_SHA          Default commit SHA (optional)

Exit codes:
  0 on success or dry-run; 1 on parameter/IO errors.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import List, Optional, Tuple
from collections.abc import Iterable

ISSUE_RE = re.compile(r"#(?P<num>\d+)")


def get_commit_message(
    explicit_sha: str | None = None, explicit_msg: str | None = None
) -> tuple[str, str]:
    """Return (sha, message) for the target commit.

    Prefers the explicitly provided message/sha; falls back to GITHUB_SHA and
    `git log -1` if not provided.
    """
    if explicit_msg is not None:
        return explicit_sha or os.environ.get("GITHUB_SHA", "HEAD"), explicit_msg

    sha = explicit_sha or os.environ.get("GITHUB_SHA")
    if not sha:
        # Resolve HEAD to a SHA
        try:
            sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
        except Exception as exc:
            print(f"[auto-issue-comment] error resolving HEAD: {exc}", file=sys.stderr)
            raise SystemExit(1)

    try:
        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B", sha], text=True
        ).strip()
    except Exception as exc:
        print(
            f"[auto-issue-comment] error reading commit message: {exc}", file=sys.stderr
        )
        raise SystemExit(1)

    return sha, msg


def parse_issue_numbers(message: str) -> list[int]:
    return [int(m.group("num")) for m in ISSUE_RE.finditer(message)]


def post_comment(
    repo: str, issue_number: int, body: str, token: str | None
) -> tuple[int, str, dict]:
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    data = json.dumps({"body": body}).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.getcode(), payload.get("html_url", ""), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore"), dict(e.headers)
    except urllib.error.URLError as e:
        return 0, str(e), {}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Annotate issues referenced by commit messages"
    )
    parser.add_argument(
        "--commit", dest="commit", default=None, help="Commit SHA to read"
    )
    parser.add_argument(
        "--message", dest="message", default=None, help="Explicit message text"
    )
    parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true", help="Do not call GitHub API"
    )
    parser.add_argument(
        "--body-prefix", dest="prefix", default="", help="Prefix for the comment body"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    sha, msg = get_commit_message(args.commit, args.message)
    issues = parse_issue_numbers(msg)

    if not issues:
        print(
            "[auto-issue-comment] no issue references found in commit message; nothing to do"
        )
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    dry_run = args.dry_run or not token or not repo

    body = f"{args.prefix}Commit {sha} referenced this issue.\n\n> {msg.strip()}\n\n— automated notice by scripts/auto_issue_comment.py"

    for num in issues:
        if dry_run:
            print(
                f"[auto-issue-comment] dry-run: would comment on {repo or '<unknown>'}#%d"
                % num
            )
            continue
        code, text, headers = post_comment(repo, num, body, token)
        remaining = headers.get("x-ratelimit-remaining")
        if remaining is not None:
            print(f"[auto-issue-comment] rate-limit remaining: {remaining}")
        if code == 201:
            print(f"[auto-issue-comment] commented on #{num}: {text}")
        elif code in (403, 429):
            print(
                f"[auto-issue-comment] rate limited; skipping further comments: {text}"
            )
            break
        elif code == 0:
            print(
                f"[auto-issue-comment] network error: {text}; continuing in best-effort mode"
            )
        else:
            print(
                f"[auto-issue-comment] non-201 status ({code}) for issue #{num}: {text}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
