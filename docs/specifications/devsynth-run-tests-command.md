---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-17
status: review
tags:
  - specification
title: devsynth run-tests command
version: 0.1.0a1
---

# Summary
Enhances `devsynth run-tests` with flags to control parallelism, batching, and feature toggles.

## Socratic Checklist
- **What is the problem?** Developers lacked fine-grained control over test execution; optional providers could stall runs, large suites overwhelmed resources, and conditional features were hard to toggle.
- **What proofs confirm the solution?** Behavior tests invoke the command with `--no-parallel`, `--segment`, and `--feature` options; unit tests verify feature flag parsing.

## Motivation

## What proofs confirm the solution?
- Behavior-driven regression packs exercise CLI happy paths, optional-provider skips, reporting, and segmentation through [`tests/behavior/features/devsynth_run_tests_command.feature`](../../tests/behavior/features/devsynth_run_tests_command.feature) and [`tests/behavior/features/general/run_tests.feature`](../../tests/behavior/features/general/run_tests.feature), with step bindings loaded by [`tests/behavior/test_run_tests_cli_report_and_segmentation.py`](../../tests/behavior/test_run_tests_cli_report_and_segmentation.py) and [`tests/behavior/test_run_tests.py`](../../tests/behavior/test_run_tests.py).
- Unit suites cover flag translation and subprocess orchestration, including feature toggles ([`tests/unit/application/cli/commands/test_run_tests_features.py`](../../tests/unit/application/cli/commands/test_run_tests_features.py)), provider defaults ([`tests/unit/application/cli/commands/test_run_tests_provider_defaults.py`](../../tests/unit/application/cli/commands/test_run_tests_provider_defaults.py)), segmentation mechanics ([`tests/unit/testing/test_run_tests_segmented.py`](../../tests/unit/testing/test_run_tests_segmented.py)), and parallel execution fallbacks ([`tests/unit/testing/test_run_tests_parallel_flags.py`](../../tests/unit/testing/test_run_tests_parallel_flags.py)).
- Property-based checks guard node-id sanitization so segmented execution cannot overrun pytest selectors ([`tests/property/test_run_tests_sanitize_properties.py`](../../tests/property/test_run_tests_sanitize_properties.py)).
- Finite state transitions and bounded loops guarantee termination; the invariant summary in [`docs/implementation/run_tests_cli_invariants.md`](../implementation/run_tests_cli_invariants.md) documents the supporting coverage evidence and failure-mode proofs.

Reliable test runs require bypassing unavailable providers, splitting large suites, and enabling optional features via environment flags.

## Specification
- `--no-parallel` disables `pytest-xdist` so tests run sequentially.
- `--segment` runs tests in batches; `--segment-size` sets batch size (default 50).
- `--feature NAME[=BOOLEAN]` sets `DEVSYNTH_FEATURE_<NAME>` to `true` or `false` for the test process.
- Optional providers are disabled by default unless their `DEVSYNTH_RESOURCE_*` variables are explicitly set.
- `--report` emits HTML and JSON coverage artifacts summarizing executed speed profiles for audit trails.
- Successful runs enforce a minimum coverage threshold of `DEFAULT_COVERAGE_THRESHOLD` (90%) whenever coverage instrumentation is active; the CLI prints a success banner when the gate is met and exits with an error if coverage falls below the limit.

## Acceptance Criteria
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel` completes without waiting on optional providers.
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel --segment --segment-size=1` executes tests in batches of one.
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel --feature demo=false` sets `DEVSYNTH_FEATURE_DEMO=false` during test execution.
- Invocations without `--no-parallel` run tests in parallel while still skipping optional providers.
- `devsynth run-tests --target unit-tests --speed=fast --report` emits `test_reports/report.html` and `test_reports/coverage.json` artifacts that list executed speed profiles.
- When coverage instrumentation reports at least 90% coverage, the CLI prints the "Coverage XX.XX% meets the 90% threshold" success banner; otherwise the command exits non-zero and includes a helpful error message.
