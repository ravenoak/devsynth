---
author: DevSynth Team
date: "2025-08-25"
status: draft
title: Flaky Case Log (Dialectical Notes)
version: "0.1.0a1"
---
# Flaky Case Log (Dialectical Notes)

Purpose: Capture brief dialectical notes for flaky test fixes to improve shared understanding and prevent regressions. Format per task 46 in docs/tasks.md.

Legend:
- Thesis: Initial hypothesis about the cause
- Antithesis: Counter-evidence found during investigation
- Synthesis: Final change implemented

Entries reference mitigations codified in tests/conftest.py, project guidelines, and docs/plan.md.

## FC-01: Non-deterministic random usage
- Thesis: Randomized inputs cause intermittent failures.
- Antithesis: Some failures reproduced even with fixed seeds; numpy and Python RNG not both seeded.
- Synthesis: Enforced deterministic_seed autouse fixture; seed both random and numpy, documented in testing guide.

## FC-02: Wall-clock timing drift
- Thesis: Time-sensitive assertions fail due to local timezone/clock skew.
- Antithesis: Failures persisted across UTC-aligned environments.
- Synthesis: Introduced mock_datetime fixture; replaced now() calls in tests; added note to docs about freezegun alternatives.

## FC-03: Outbound network egress
- Thesis: Unexpected HTTP requests cause timeouts on CI.
- Antithesis: requests-mocked tests still triggered low-level sockets.
- Synthesis: Added disable_network autouse fixture blocking socket.connect, urllib, and httpx; preserved requests compatibility with responses; documented gating via requires_resource.

## FC-04: Plugin autoload conflicts
- Thesis: Third-party pytest plugins cause hangs and arg parsing errors.
- Antithesis: Only in smoke runs with plugin options present in pytest.ini.
- Synthesis: Ensure PYTEST_DISABLE_PLUGIN_AUTOLOAD only set in CLI smoke mode; removed unconditional disabling from core runner; updated CLI docs and behavior tests.

## FC-05: Coverage + xdist teardown KeyError
- Thesis: Coverage plugin breaks parallel teardown.
- Antithesis: Serial runs stable; only parallel workers fail.
- Synthesis: Disable coverage under parallel execution (run-tests adds --no-cov when -n auto used); documented in testing guide.

## FC-06: Global state leakage between tests
- Thesis: Modules retain state across tests order.
- Antithesis: Reordering reproduces failures intermittently.
- Synthesis: Implemented reset_global_state and global_test_isolation autouse fixture resetting env, CWD, HOME, and known globals; documented guarantees.

## FC-07: Stray filesystem artifacts
- Thesis: Tests write to repo root .devsynth/logs.
- Antithesis: Happens despite tmp_path usage in some paths.
- Synthesis: global_test_isolation redirects HOME and XDG paths to tmp; patches Path.home(); post-test cleanup removes artifacts if created; added docs and checks.

## FC-08: Slow/hanging tests in fast lane
- Thesis: Some fast tests occasionally hang on slower machines.
- Antithesis: Not reproducible under profiler but recurs in CI.
- Synthesis: enforce_test_timeout autouse with env-configurable seconds; run-tests CLI sets conservative defaults in smoke/fast; documented override.

## FC-09: Parametrized tests mis-marked
- Thesis: Verifier flags parametrized tests despite function-level marker.
- Antithesis: Marks applied only to some parameters via pytest.param.
- Synthesis: Normalize to single function-level speed marker or uniform pytest.param marks; enhanced docs and added examples; ran scripts/verify_test_markers.py to confirm.

## FC-10: Behavior tests with no matches
- Thesis: Runner fails with "no tests ran" when filtering by unused speed.
- Antithesis: Only behavior-tests target exhibits brittle behavior.
- Synthesis: Fallback logic in run_tests.collect_tests_with_cache broadens selection for behavior target when none match; acceptance covered by behavior tests and docs.

## FC-11: Resource-dependent test nondeterminism
- Thesis: Optional backends intermittently available locally.
- Antithesis: Skips inconsistent due to env not set.
- Synthesis: Default DEVSYNTH_RESOURCE_* flags to false in CLI; tests rely on requires_resource; added quick recipes in testing guide to enable locally.

References:
- project guidelines
- docs/plan.md
- docs/developer_guides/testing.md
- tests/conftest.py
