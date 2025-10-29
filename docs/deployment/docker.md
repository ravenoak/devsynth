---
title: "Docker Build and Runtime Guide"
date: 2025-08-24
version: 0.1.0a1
status: published
last_reviewed: 2025-08-24
---

# Docker Build and Runtime Guide

This guide explains how to build and run the DevSynth Docker image using the multi-stage Dockerfile in the project root.

## Overview

The Dockerfile defines multiple stages:
- base: Common runtime dependencies and Poetry
- builder: Installs project dependencies into a local virtualenv (.venv)
- development: Brings in source, tests, docs, and tools for local development
- testing: Ensures dev extras for running the test suite
- production: Minimal runtime with project installed via Poetry virtualenv

## Building

Build the development image (contains source and tests):

```bash
docker build -t devsynth:dev --target development .
```

Build the testing image:

```bash
docker build -t devsynth:test --target testing .
```

Build the production image (minimal):

```bash
docker build -t devsynth:latest --target production .
```

## Running

By default, the production image runs a safe, minimal command to verify installation:

```bash
docker run --rm devsynth:latest
# Equivalent to: poetry run devsynth --help
```

Override the command to run specific CLI subcommands:

```bash
docker run --rm devsynth:latest poetry run devsynth help
```

For interactive usage:

```bash
docker run -it --rm -v "$PWD":/workspace -w /workspace devsynth:dev bash
```

## Ports and Services

- The production image does not start a network service by default.
- To run an API or WebUI in the future, override the CMD with the appropriate entrypoint after enabling the corresponding extras/feature flags.

## Notes

- The image uses a non-root user by default for better security.
- Heavy optional dependencies are not imported at startup, aligning with safe-by-default provider settings.
- If you need GPU or additional extras, use Poetry extras and modify the Docker build arguments accordingly.

## Troubleshooting

- If build layers are invalidated frequently, ensure pyproject.toml and poetry.lock are copied before source to maximize caching.
- For CI usage, prefer target=testing for running the test suite inside the container.
