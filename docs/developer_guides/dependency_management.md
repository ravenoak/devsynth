---

title: "Dependency Management"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "development"
  - "dependencies"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Dependency Management
</div>

# Dependency Management

This guide explains how DevSynth manages third-party Python packages.

## Installing Dependencies

DevSynth uses [Poetry](https://python-poetry.org/) for dependency
management. Install all project requirements with:

```bash
poetry install
```

## Updating Dependencies

To update packages to the latest compatible versions and refresh
`poetry.lock`, run:

```bash
poetry update
```

Alternatively, execute the helper script:

```bash
python scripts/dependency_safety_check.py --update
```

This script runs `poetry update` and then performs a vulnerability
check using the `safety` tool.

## Checking for Vulnerabilities

Regularly scan dependencies with:

```bash
python scripts/dependency_safety_check.py
```

The script exports the current dependencies, then invokes
`safety check` to report known security issues.

## Pinning Versions

All dependency versions are pinned in `pyproject.toml` to ensure
reproducible builds. After modifying dependencies, commit the updated
`poetry.lock` file.
## Implementation Status

.
