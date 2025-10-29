---

title: "Dependency Strategy"
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
  - **`webui`** – Installs the NiceGUI-based WebUI.
  - **`gui`** – Installs the Dear PyGui-based desktop UI.
- **`lmstudio`** – Adds the LM Studio provider integration. Tests depending on
  LM Studio are skipped when this extra is not installed.
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
poetry install --with dev --extras "tests retrieval chromadb api"
```

If your platform cannot build the retrieval extras (common when FAISS, Kuzu,
or ChromaDB wheels are unavailable), fall back to the tests-only profile and
explicitly disable the heavy resources until wheels are published:

```bash
poetry install --with dev --extras "tests"
export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=false
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false
```

This keeps the fast and medium suites runnable in CI while preserving the
coverage instrumentation hooks. Re-enable the environment flags once the
corresponding extras are installed successfully.

From PyPI you can simply run:

```bash
pip install devsynth
```

Extras can be enabled later with `poetry install --extras llm --extras api --extras gui` or `pip install 'devsynth[llm,api,gui]'`.

## Checking for Updates

Run `python scripts/dependency_safety_check.py` to scan for vulnerabilities. CI also executes this script to detect breaking updates whenever the dependency files change.

## Implementation Status

- Status: documentation upkeep ongoing
