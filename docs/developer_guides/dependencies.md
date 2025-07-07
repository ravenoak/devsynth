---
title: "Dependency Strategy"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "development"
  - "dependencies"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# Dependency Strategy

This document describes how DevSynth manages Python package dependencies and optional features.

## Core Dependencies

All core packages are pinned in `pyproject.toml` to guarantee reproducible builds. After changing dependencies, commit the updated `poetry.lock` file.

## Optional Extras

Some features rely on additional packages. These dependencies are grouped using [Poetry extras](https://python-poetry.org/docs/pyproject/#extras). Install them when needed:

- **`retrieval`** – Provides vector store backends such as ChromaDB and FAISS.
- **`memory`** – Installs Kuzu, LMDB, FAISS, and related memory backends.
- **`llm`** – Optional helpers for provider integrations.
- **`dsp`** – Experimental [DSPy](https://github.com/stanford-oval/dspy) integration.
- **`dev`** and **`docs`** – Development and documentation tooling.


Example installation:

```bash
poetry add "devsynth[dev,retrieval]"
```

## Checking for Updates

Run `python scripts/dependency_safety_check.py` to scan for vulnerabilities. CI also executes this script to detect breaking updates whenever the dependency files change.

