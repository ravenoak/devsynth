---
title: "Dependency Strategy"
date: "2025-06-01"
version: "0.1.0"
tags:
  - "development"
  - "dependencies"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---

# Dependency Strategy

This document describes how DevSynth manages Python package dependencies and optional features.

## Core Dependencies

All core packages are pinned in `pyproject.toml` to guarantee reproducible builds. After changing dependencies, commit the updated `poetry.lock` file.

## Optional Extras

Some features rely on additional packages. These dependencies are grouped using [Poetry extras](https://python-poetry.org/docs/pyproject/#extras). Install them when needed:

- **`retrieval`** – Provides vector store backends such as ChromaDB and FAISS.
- **`memory`** – Installs Kuzu, LMDB, FAISS, NumPy, and related memory backends.
- **`llm`** – Optional helpers for provider integrations and offline LLM support via `torch` and `transformers`.
- **`api`** – Enables the FastAPI server and Prometheus metrics.
- **`webui`** – Installs the Streamlit-based WebUI.
- **`lmstudio`** – Adds the LM Studio provider integration.
- **`dsp`** – Experimental [DSPy](https://github.com/stanford-oval/dspy) integration.
- **`dev`** and **`docs`** – Development and documentation tooling.


Example installation:

```bash
poetry add "devsynth[dev,retrieval]"
```

## Minimal Installation

Install only the core runtime without optional extras:

```bash
poetry install --without dev --without docs
```

From PyPI you can simply run:

```bash
pip install devsynth
```

Extras can be enabled later with `poetry install --extras llm --extras api` or `pip install 'devsynth[llm,api]'`.

## Checking for Updates

Run `python scripts/dependency_safety_check.py` to scan for vulnerabilities. CI also executes this script to detect breaking updates whenever the dependency files change.

## Implementation Status

This feature is **planned** and not yet implemented.
