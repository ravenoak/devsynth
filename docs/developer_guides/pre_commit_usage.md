---
title: "Pre-commit Usage"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "pre-commit"
  - "hooks"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Pre-commit Usage
</div>

# Pre-commit Usage

The DevSynth project uses [pre-commit](https://pre-commit.com/) to run checks before code is committed.
Install the hooks with:

```bash
pre-commit install
```

Run all checks with:

```bash
pre-commit run --all-files
```

## Custom Hooks

### check internal links

Runs `python scripts/check_internal_links.py` to verify that Markdown files do not contain broken internal links.

### fix code blocks

Runs `python scripts/fix_code_blocks.py --check` to ensure code block formatting is consistent.

### find syntax errors

Runs `python scripts/find_syntax_errors.py` to detect Python syntax errors across the repository.

### commit message lint

Runs `python scripts/commit_linter.py` during the `commit-msg` stage to ensure
commit messages follow Conventional Commits and MVUU requirements. To lint a
range of commits manually, run:

```bash
python scripts/commit_linter.py --range origin/main..HEAD
```
