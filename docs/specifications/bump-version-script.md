---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:
- specification
title: Version bump script
version: 0.1.0a1
---

<!--
Required metadata fields:
- author: document author
- date: creation date
- last_reviewed: last review date
- status: draft | review | published
- tags: search keywords
- title: short descriptive name
- version: specification version
-->

# Summary

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/bump_version_script.feature`](../../tests/behavior/features/bump_version_script.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.


After cutting a release tag, developers need a consistent way to bump the project to the next development version.

## Specification

- Provide `scripts/bump_version.py` which wraps `poetry version <new_version>`.
- After bumping, rewrite `src/devsynth/__init__.py` so `__version__` matches the new version.

## Acceptance Criteria

- Running `python scripts/bump_version.py 0.1.0-alpha.2.dev0` updates `src/devsynth/__init__.py` to `__version__ = "0.1.0-alpha.2.dev0"`.
- The script exits with status `0` when the update succeeds.
