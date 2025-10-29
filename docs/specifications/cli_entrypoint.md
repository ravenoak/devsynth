---
author: AI Assistant
date: 2025-08-23
last_reviewed: 2025-08-24
status: draft
tags:
  - specification
  - cli

title: CLI Entrypoint
version: 0.1.0a1
---

Feature: CLI Entrypoint

# Summary

The CLI entrypoint module provides a minimal interface for repository analysis or delegating to the Typer-based CLI.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/cli_entrypoint.feature`](../../tests/behavior/features/cli_entrypoint.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

The project requires a single entrypoint capable of lightweight repository analysis without loading the full command stack.

## Specification
- Provide an `--analyze-repo` option that outputs JSON analysis for a given path.
- Otherwise delegate to the main Typer CLI.

## Acceptance Criteria
- Running `devsynth --analyze-repo PATH` emits JSON describing the repository.
- Invoking `devsynth` without options runs the Typer CLI.

## References

- [Issue: Dialectical audit documentation](../../issues/dialectical-audit-documentation.md)
- [BDD: cli_entrypoint.feature](../../tests/behavior/features/cli_entrypoint.feature)
