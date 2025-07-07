---
author: DevSynth Team
date: '2025-06-01'
last_reviewed: '2025-06-01'
status: published
tags:

- installation
- getting started
- setup
- configuration

title: DevSynth Installation Guide
version: 1.0.0
---

# DevSynth Installation Guide

## Executive Summary

This guide provides step-by-step instructions for installing DevSynth in various environments. It covers installation via PyPI and from source, along with prerequisites for both methods.

## Prerequisites

- Python 3.11 or higher
- Poetry (recommended for development)


## Install from PyPI using Poetry

```bash
poetry add devsynth
```

### Install with pipx *(end-user install)*

```bash
pipx install devsynth
```

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