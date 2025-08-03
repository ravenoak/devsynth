---
title: "Dependency Strategy"
date: "2025-06-01"
version: "0.1.0"
tags:
  - "development"
  - "dependencies"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Dependency Strategy
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Dependency Strategy
</div>

# Dependency Strategy

This document describes how DevSynth manages Python package dependencies and optional features.

## Core Dependencies

All core packages are pinned in `pyproject.toml` to guarantee reproducible builds. After changing dependencies, commit the updated `poetry.lock` file.

## Optional Extras

Some features rely on additional packages. These dependencies are grouped using [Poetry extras](https://python-poetry.org/docs/pyproject/#extras). Install them when needed:

- **`retrieval`** – Provides vector store backends such as ChromaDB and FAISS.
- **`memory`** – Installs Kuzu, LMDB, FAISS, NumPy, and related memory backends.
- **`llm`** – Helpers for remote provider integrations.
- **`offline`** – Enables deterministic offline mode. Combine with `gpu` to load local models.
- **`gpu`** – Installs `torch` and NVIDIA libraries for hardware acceleration.
- **`api`** – Enables the FastAPI server and Prometheus metrics.
- **`webui`** – Installs the Streamlit-based WebUI.
- **`dpgui`** – Installs the Dear PyGui-based desktop UI.
- **`lmstudio`** – Adds the LM Studio provider integration.
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

For contributing to DevSynth a lightweight setup is often sufficient:

```bash
poetry install --with dev --extras minimal
```

From PyPI you can simply run:

```bash
pip install devsynth
```

Extras can be enabled later with `poetry install --extras llm --extras api --extras dpgui` or `pip install 'devsynth[llm,api,dpgui]'`.

## Checking for Updates

Run `python scripts/dependency_safety_check.py` to scan for vulnerabilities. CI also executes this script to detect breaking updates whenever the dependency files change.

## Implementation Status

.
