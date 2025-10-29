---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:
- specification
title: Release state check
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
- BDD scenarios in [`tests/behavior/features/release_state_check.feature`](../../tests/behavior/features/release_state_check.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.


Ensure release documentation marked as published has a corresponding Git tag.

## Specification

- Parse `docs/release/0.1.0-alpha.1.md` to read its `status` and `version`.
- When `status` is `published`, verify a tag matching `v<version>` exists.
- Fail with a non-zero exit code when the tag is missing.

## Acceptance Criteria

- Running `python scripts/verify_release_state.py` exits with status `1` when the release is marked as published and tag `v0.1.0-alpha.1` does not exist.
- The script exits with status `0` otherwise.
