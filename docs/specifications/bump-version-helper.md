---
author: DevSynth Team
date: '2025-08-19'
last_reviewed: '2025-08-19'
status: draft
tags:
  - specification
  - release
title: Version Bump Helper
---

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation
Automating version bumps reduces manual steps and keeps project metadata in sync after a release tag.

## Specification
- A script `scripts/bump_version.py` accepts a target version string.
- The script executes `poetry version <version>` to update `pyproject.toml`.
- It updates `src/devsynth/__init__.py` so `__version__` matches the new version.

## Acceptance Criteria
- Running `python scripts/bump_version.py 0.1.0-alpha.2.dev0` updates Poetry and `__init__.py` to `0.1.0-alpha.2.dev0`.
- The script exits with an error if `poetry version` fails or the update cannot be written.
