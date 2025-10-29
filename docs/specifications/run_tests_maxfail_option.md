---
title: "Run Tests Maxfail Option"
author: "DevSynth Team"
date: "2025-07-14"
last_reviewed: "2025-07-14"
status: draft
version: "0.1.0a1"
tags:
  - specification
  - testing
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Run Tests Maxfail Option
</div>

# Run Tests Maxfail Option

## Summary
Adds a `--maxfail` flag to `devsynth run-tests` allowing early termination after a set number of test failures.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/run_tests_maxfail_option.feature`](../../tests/behavior/features/run_tests_maxfail_option.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

Quick feedback loops benefit from stopping test execution after the first few failures, but the DevSynth CLI lacked this control.

## Specification
- The `devsynth run-tests` command accepts `--maxfail <n>`.
- The value is forwarded to pytest's `--maxfail` option.
- When omitted, behavior matches previous releases.

## Acceptance Criteria
- `devsynth run-tests --maxfail 1` stops after a single failing test.
- Invocations without `--maxfail` run all selected tests.
