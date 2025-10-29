---
title: "Pre-commit Hook Samples"
date: "2025-08-04"
version: "0.1.0a1"
tags:
  - "pre-commit"
  - "hooks"
  - "tooling"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-04"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Pre-commit Hook Samples
</div>

# Pre-commit Hook Samples

## Overview

The DevSynth project uses [pre-commit](https://pre-commit.com/) to run automated checks before code is committed. This guide highlights common hooks used in the repository and provides a sample configuration to help you get started.

## Common Hooks

### devsynth align

Ensures files conform to project alignment rules using `devsynth align --quiet`. This hook blocks commits that introduce misaligned content.

### Link Checker

Validates external and internal links to keep documentation up to date. A typical configuration uses the [`lychee`](https://github.com/lycheeverse/lychee) hook with `--no-progress` to keep output concise.

### Formatting

Formats code and documentation automatically. The project relies on [`black`](https://github.com/psf/black) for Python code and optionally [`isort`](https://github.com/pycqa/isort) to order imports.

## Example `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: devsynth-align
        name: devsynth align
        entry: devsynth align --quiet
        language: system
        pass_filenames: false

  - repo: https://github.com/lycheeverse/lychee
    rev: v0.15.1
    hooks:
      - id: lychee
        args: [--no-progress, --verbose]

  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black
```

Use `pre-commit install` to enable these hooks locally and `pre-commit run --all-files` to run them across the entire codebase.

## Manual installation

If you prefer not to use the pre-commit framework, you can install the alignment hook directly:

```bash
ln -s ../../scripts/hooks/pre-commit-align.sh .git/hooks/pre-commit
```

This symlink runs `devsynth align --quiet` from the repository root before each commit.
