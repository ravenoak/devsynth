---

author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-08-24"
status: published
tags:

- installation
- getting started
- setup
- configuration

title: DevSynth Installation Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Installation Guide
</div>

# DevSynth Installation Guide

## Executive Summary

This guide provides step-by-step instructions for installing DevSynth in various environments. It covers installation via PyPI and from source, along with prerequisites for both methods.

> To avoid duplication with other guides, this page focuses on installation specifics. For quick commands and CLI usage details, see:
> - Quick Start: [Getting Started / Quick Start](../getting_started/quick_start_guide.md)
> - CLI options and examples: [User Guides / CLI Command Reference](../user_guides/cli_command_reference.md)

## Prerequisites

- Python 3.12.x (CI and docs assume Python 3.12)
- Poetry 1.8.x (CI uses 1.8.3; install via https://install.python-poetry.org)
- go-task ≥3.44.1 (Taskfile runner). Fresh environments may not include the `task` CLI;
  run `bash scripts/install_dev.sh`, which installs go-task and adds `$HOME/.local/bin` to your `PATH` if needed.

> Platform support: Linux and macOS are first-class development platforms. On Windows,
> we recommend Windows Subsystem for Linux (WSL2) with Ubuntu and running commands inside the WSL shell.
> Native Windows shells are not supported for developer scripts; see the Windows/WSL2 section below.

Verify that Poetry manages a virtual environment before continuing:

```bash
poetry env info --path  # should print the virtualenv path
```

If the path is empty, create it and install dependencies with:

```bash
poetry env use 3.12 && poetry install --all-extras --with dev,docs
```

Run project commands through `poetry run` or inside `poetry shell` to ensure the environment is active.

### Minimal contributor setup (fast, lightweight)

For contributors who don't need heavy optional dependencies, use the minimal extras profile:

```bash
poetry install --with dev --extras minimal
```

This aligns with the project guidelines in project guidelines and speeds up first-time setup.

See also: [Resources Matrix](../resources_matrix.md) for mapping extras to resource flags and quick enablement commands.


## Install from PyPI using Poetry

```bash
poetry add devsynth
```

### Minimal install

For a lightweight setup with only the core runtime:

```bash
poetry install --without dev --without docs
```

Extras may be added later using `poetry install --extras llm --extras api --extras offline --extras gui`.

### Optional LM Studio support

LM Studio integration is optional. Install the extra when you need it:

```bash
poetry install --extras lmstudio
```

Set `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true` to opt in to tests that require LM Studio.

### Enable GUI support

Install the optional desktop interface by including the `gui` extra:

```bash
poetry install --extras gui
```

Install the optional `gpu` extra for hardware-accelerated models:
`poetry install --extras gpu`.

### Install with pipx *(end-user install)*

```bash
pipx install devsynth
```

### Default and Fallback Modes

DevSynth is offline-safe by default. On a fresh install, remote providers are optional and not required to run core commands. A lightweight built-in provider returns deterministic responses for smoke paths and CLI help flows.

- To explicitly enable offline/local behaviors: `poetry install --extras offline` (optionally add `--extras gpu` for local accelerated models).
- To opt into remote providers, set the provider and credentials explicitly (e.g., `DEVSYNTH_PROVIDER=openai` and `OPENAI_API_KEY=...`). If credentials are missing when a remote provider is requested, startup will fail fast with a clear error.


## Install from Source (recommended for development)

```bash
git clone https://github.com/ravenoak/devsynth.git
cd devsynth

# Install with Poetry (including all extras for development)

poetry install --all-extras --with dev,docs
poetry sync --all-extras --all-groups
poetry env info --path  # confirm virtualenv
poetry shell

# Older instructions may reference `pip install -e '.[dev]'`. Use Poetry instead

# to ensure a consistent virtual environment. Pip commands are only required for

# installing from PyPI or via `pipx`.

```

## Windows / WSL2

For Windows users, install and use Windows Subsystem for Linux (WSL2) with Ubuntu:

1. Enable WSL and install Ubuntu from the Microsoft Store.
2. Install Python 3.12 and Poetry inside WSL (Ubuntu).
3. Clone this repository inside your WSL filesystem (e.g., /home/<user>/devsynth).
4. Run all commands from the Ubuntu shell. The scripts/install_dev.sh script will exit with a helpful message if run from a native Windows shell.

Known limitations:
- Native Windows shells (PowerShell/cmd) are not supported for developer scripts.
- Paths with drive letters (e.g., C:\\...) are not recognized by POSIX shell scripts; use WSL paths.

## Running the Full Test Suite

To execute all tests you need the optional packages installed by the `dev`
extras. Key dependencies include `RDFLib`, `TinyDB`, `ChromaDB`, `astor`, and
`networkx`. Install them along with the project:

```bash
poetry install --all-extras --with dev,docs
```

For more details, see the [Quick Start Guide](../getting_started/quick_start_guide.md).
## Implementation Status

Validated instructions on 2025-08-25 with Python 3.12 and Poetry on macOS 14 and Ubuntu 22.04:
- poetry install --all-extras --with dev,docs succeeded and created a virtualenv.
- devsynth --help executed via poetry run successfully with offline defaults.
- devsynth run-tests --smoke --speed=fast collected tests without network access.

This confirms the Getting Started setup produces a working environment as described.
