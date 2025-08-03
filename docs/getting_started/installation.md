---
author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-07-10"
status: published
tags:

- installation
- getting started
- setup
- configuration

title: DevSynth Installation Guide
version: 0.1.0---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Installation Guide
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Installation Guide
</div>

# DevSynth Installation Guide

## Executive Summary

This guide provides step-by-step instructions for installing DevSynth in various environments. It covers installation via PyPI and from source, along with prerequisites for both methods.

## Prerequisites

- Python 3.12 or higher
- Poetry (recommended for development)


## Install from PyPI using Poetry

```bash
poetry add devsynth
```

### Minimal install

For a lightweight setup with only the core runtime:

```bash
poetry install --without dev --without docs
```

Extras may be added later using `poetry install --extras llm --extras api --extras offline`.
Install the optional `gpu` extra for hardware-accelerated models:
`poetry install --extras gpu`.

### Install with pipx *(end-user install)*

```bash
pipx install devsynth
```
### Fallback Modes

Without the `offline` extra, DevSynth uses a lightweight built-in provider that returns deterministic responses. Install with `poetry install --extras offline` and optionally `--extras gpu` to enable local models via `transformers` and `torch`.


## Install from Source (recommended for development)

```bash
git clone https://github.com/ravenoak/devsynth.git
cd devsynth

# Install with Poetry (including all extras for development)

poetry install --all-extras --with dev,docs
poetry sync --all-extras --all-groups
poetry shell

# Older instructions may reference `pip install -e '.[dev]'`. Use Poetry instead

# to ensure a consistent virtual environment. Pip commands are only required for

# installing from PyPI or via `pipx`.

```

## Running the Full Test Suite

To execute all tests you need the optional packages installed by the `dev`
extras. Key dependencies include `RDFLib`, `TinyDB`, `ChromaDB`, `astor`, and
`networkx`. Install them along with the project:

```bash
poetry install --all-extras --with dev,docs
```

For more details, see the [Quick Start Guide](../getting_started/quick_start_guide.md).
## Implementation Status

.
