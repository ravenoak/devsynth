---
author: DevSynth Team
date: '2025-08-21'
last_reviewed: '2025-08-21'
status: draft
tags:
- development
- setup
- virtualenv
- guide
- tooling
title: Virtual Environment Enforcement
description: Ensure all development runs inside the Poetry-managed virtual environment.
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Virtual Environment Enforcement
</div>

# Virtual Environment Enforcement

Consistent tooling requires every command to run inside the project's Poetry-managed virtual environment.
This guide explains how to enforce that environment and avoid using the global Python interpreter.

## Configure Poetry to Create Virtual Environments

Ensure Poetry always creates a dedicated virtual environment:

```bash
poetry config virtualenvs.create true
```

## Activate the Environment

Use `poetry run` to prefix commands or spawn a shell within the virtual environment:

```bash
poetry shell
# or run a single command
poetry run pytest
```

## Why It Matters

Running tools outside the virtual environment can lead to version drift and missing dependencies.
Enforcing the virtual environment keeps development reproducible and aligns with the dialectical audit requirements.

## Implementation Status

- Status: documented
