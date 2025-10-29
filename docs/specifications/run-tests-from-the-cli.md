---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-10-09
status: review
tags:

- specification

title: Run tests from the CLI
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

`devsynth run-tests` must keep segmentation predictable even when discovery
returns no node identifiers. The CLI funnels every invocation through a single
code path that injects coverage plugins, guards marker discipline, and
falls back to a non-segmented batch when prerequisites are missing.

## Socratic Checklist
- **What is the problem?** Segmentation previously propagated truthy flags to
  `run_tests`, but when no speed filters were provided the helper still
  expected batched execution, leading to confusing marker-fallback behavior and
  missing regression coverage for the CLI contract.
- **What proofs confirm the solution?** Behavior and unit suites assert the CLI
  forwards segmentation intent, the helper collapses to a single batch when no
  speed filters are active, and regression cases cover HTML report hints,
  plugin reinjection, and failure tips.

## Motivation

Developers rely on `devsynth run-tests` to triage failures quickly. When the
CLI surfaces segmentation knobs it must also document when segmentation is
silently disabled so that coverage sweeps and retry loops remain predictable.

## What proofs confirm the solution?
- BDD scenarios in
  [`tests/behavior/features/run_tests_from_the_cli.feature`](../../tests/behavior/features/run_tests_from_the_cli.feature)
  exercise segmentation without speed filters and confirm the CLI records the
  fallback semantics; they execute via
  [`tests/behavior/test_run_tests_from_cli.py`](../../tests/behavior/test_run_tests_from_cli.py)
  with shared steps in
  [`tests/behavior/steps/test_run_tests_cli_steps.py`](../../tests/behavior/steps/test_run_tests_cli_steps.py).
- Unit suites under
  [`tests/unit/testing/test_run_tests_segmented.py`](../../tests/unit/testing/test_run_tests_segmented.py)
  verify that `_run_segmented_tests` stops after the first failing batch when
  `maxfail` is specified, ensuring coverage for the early-exit branch exercised
  by the CLI segmentation contract.
- Regression packs for reporting (`test_run_tests_cli_report_and_segmentation.py`)
  and coverage helpers (`test_run_tests_cli_helpers_focus.py`) remain green,
  confirming the CLI surface matches documented behavior.

## Specification
- CLI segmentation (`--segment` / `--segment-size`) is opt-in and requires at
  least one explicit speed filter (`--speed`). Without speed filters the helper
  performs a single batch run and annotates the output with "Marker fallback
  executed." before returning results.
- When segmentation is disabled because of fallback conditions the CLI still
  forwards the requested `segment_size` for observability while preserving the
  non-parallel execution mode selected by the user.
- Failures encountered during segmented execution respect the `--maxfail`
  threshold by aborting remaining batches after the first failing segment.

## Acceptance Criteria
- Invoking
  `devsynth run-tests --target unit-tests --segment --segment-size=3 --no-parallel`
  without `--speed` runs exactly one batch and records the segmentation
  fallback in the helper invocation context.
- Segmented execution with `--speed` provided continues to batch node IDs and
  reinjects coverage plugins exactly once per batch.
- When `--maxfail` is supplied the helper stops after the first failing batch
  and surfaces troubleshooting tips exactly once per failed segment.
