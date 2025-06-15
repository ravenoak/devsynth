---
title: "DevSynth Example Project"
date: "2025-07-01"
version: "1.0.0"
tags:
  - "getting-started"
  - "example"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-01"
---

# DevSynth Example Project

This guide walks through a small calculator example included in the `examples/` directory. It demonstrates project initialization, specification and test generation, code creation, and running the final program.

## Location

The example lives in [`examples/calculator`](../../examples/calculator). Each file shows what you would have after running DevSynth commands.

For a complete demonstration of the adaptive workflow, see the full workflow example in [`examples/full_workflow`](../../examples/full_workflow).

## Workflow Overview

1. **Initialize** the project
   ```bash
   cd examples/calculator
   devsynth init --path .
   ```
   The command now launches an interactive wizard when run in an existing directory and will read any `pyproject.toml` or `devsynth.yml` it detects.
2. **Generate specifications** from the requirements
   ```bash
   devsynth spec --requirements-file requirements.md
   ```
3. **Generate tests**
   ```bash
   devsynth test
   ```
4. **Generate code**
   ```bash
   devsynth code
   ```
5. **Run** the project
   ```bash
   devsynth run
   ```

The repository contains the resulting `specs.md`, tests in `tests/`, and code in `src/`. You can modify the requirements and re-run the DevSynth commands to update the project.

## Continuous Integration Example

The `.github/workflows/example_project.yml` file provides a minimal CI setup that runs the same DevSynth commands on every push or pull request affecting the example. Use it as a starting point for your own projects.
