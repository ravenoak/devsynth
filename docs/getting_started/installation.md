---
title: "DevSynth Installation Guide"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "installation"
  - "getting started"
  - "setup"
  - "configuration"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# Installation Guide

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

# Install with Poetry
poetry install --with dev,docs
poetry sync --all-extras --all-groups
poetry shell

# pip commands are for installing from PyPI only
```

### Running the Full Test Suite

To execute all tests you need the optional packages installed by the `dev`
extras. Key dependencies include `rdflib`, `tinydb`, `chromadb`, `astor`, and
`networkx`. Install them along with the project:

```bash
poetry install --with dev,docs
```

For more details, see the [Quick Start Guide](../getting_started/quick_start_guide.md).
