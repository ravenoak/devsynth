---
author: DevSynth Team
date: "2025-08-25"
status: reference
version: "0.1.0a1"
---
# Flaky Tests: Root Causes and Mitigations

This document catalogs known sources of test flakiness in DevSynth and the mitigations we apply. It aligns with project guidelines (determinism, isolation) and the stabilization plan in docs/plan.md.

## Symptoms Observed
- Intermittent timeouts when third-party plugins are active.
- Occasional filesystem pollution outside tmp directories.
- Rare network egress attempts when provider defaults are overridden locally.

## Root Causes
1. Non-deterministic timing in parallel/xdist runs on busy CI machines.
2. Hidden global state and writes to HOME or project directories.
3. Accidental network calls from optional HTTP clients when offline toggles aren’t set.

## Mitigations (Implemented)
- Autouse fixtures in tests/conftest.py:
  - global_test_isolation: redirects HOME/XDG paths to tmp; patches Path.home(); ensures tmp-only writes; restores env and CWD after each test.
  - disable_network: blocks sockets, urllib, requests, and httpx to enforce hermetic tests.
  - enforce_test_timeout: optional per-test timeout via DEVSYNTH_TEST_TIMEOUT_SECONDS.
- CLI smoke mode: devsynth run-tests --smoke --speed=fast disables third-party plugins and xdist.
- Speed marker discipline: exactly one of @pytest.mark.fast|medium|slow per test; violations gated by scripts/verify_test_markers.py.

## Additional Guidance
- Prefer deterministic waits (event polling with bounded retries) over hard sleeps.
- Avoid relying on wall-clock; use monotonic timers (time.perf_counter) and fake time where feasible.
- For resource-gated tests, mark with @pytest.mark.requires_resource("<NAME>") and honor DEVSYNTH_RESOURCE_* flags; default to skip.
- When adding new IO tests, write only under tmp_path provided by pytest fixtures.

## Operator Playbook
- If a test flakes in CI:
  1. Re-run in smoke mode to reduce plugin surface:
     poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  2. Enable per-test timeout to catch slow paths:
     DEVSYNTH_TEST_TIMEOUT_SECONDS=30 poetry run devsynth run-tests --target unit-tests --speed=fast
  3. Inspect artifacts and logs (if enabled via explicit opt-in local runs).

## Status
- Flakiness mitigations are active by default in tests/conftest.py.
- Documented here to close docs/tasks.md item 5.4 with actionable steps.
