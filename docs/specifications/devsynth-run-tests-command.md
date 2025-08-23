---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:
  - specification
title: devsynth run-tests command
version: 0.1.0-alpha.1
---

# Summary
Enhances `devsynth run-tests` with flags to control parallelism, batching, and feature toggles.

Runtime behavior and termination characteristics are analyzed in [analysis/run_tests_workflow_analysis.md](../analysis/run_tests_workflow_analysis.md).

## Socratic Checklist
- **What is the problem?** Developers lacked fine-grained control over test execution; optional providers could stall runs, large suites overwhelmed resources, and conditional features were hard to toggle.
- **What proofs confirm the solution?** Behavior tests invoke the command with `--no-parallel`, `--segment`, and `--feature` options; unit tests verify feature flag parsing.

## Motivation
Reliable test runs require bypassing unavailable providers, splitting large suites, and enabling optional features via environment flags.

## Specification
- `--no-parallel` disables `pytest-xdist` so tests run sequentially.
- `--segment` runs tests in batches; `--segment-size` sets batch size (default 50).
- `--feature NAME[=BOOLEAN]` sets `DEVSYNTH_FEATURE_<NAME>` to `true` or `false` for the test process.
- Optional providers are disabled by default unless their `DEVSYNTH_RESOURCE_*` variables are explicitly set.

## Acceptance Criteria
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel` completes without waiting on optional providers.
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel --segment --segment-size=1` executes tests in batches of one.
- `devsynth run-tests --target unit-tests --speed=fast --no-parallel --feature demo=false` sets `DEVSYNTH_FEATURE_DEMO=false` during test execution.
- Invocations without `--no-parallel` run tests in parallel while still skipping optional providers.
