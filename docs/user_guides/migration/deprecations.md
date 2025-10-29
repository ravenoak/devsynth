---
author: DevSynth Team
date: '2025-08-25'
last_reviewed: '2025-08-25'
status: stable
tags:
- migration
- deprecations
title: Deprecations and Migration Notes
version: "0.1.0a1"
---

# Deprecations and Migration Notes

This page lists practical migration guidance for deprecated commands/APIs.
For the complete deprecation policy and schedule, see docs/policies/deprecation_policy.md.

## Test Runner Wrapper

- Deprecated: `scripts/run_all_tests.py`
- Replacement: `devsynth run-tests`
- Behavior: The legacy script forwards to the CLI and emits a `DeprecationWarning`.
- Migration:
  - Replace usages of `python scripts/run_all_tests.py [args...]` with `poetry run devsynth run-tests [args...]`.
  - Feature flags: replace `--features '{"name": true}'` with repeated `--feature name=true`.
  - Prefer speed‑scoped invocations, e.g.: `poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel`.

## Other Legacy Scripts

Refer to the policy table for other scripts scheduled for removal in v1.0. Migrate to the documented `devsynth` subcommands accordingly.
