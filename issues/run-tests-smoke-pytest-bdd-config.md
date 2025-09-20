Title: Smoke run fails when pytest-bdd config not loaded
Date: 2025-09-20 14:47 UTC
Status: open
Affected Area: tests
Reproduction:
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
Exit Code: 1
Artifacts:
  - logs/run-tests-smoke-fast-20250920.log
  - logs/run-tests-smoke-fast-20250920T000000Z.log (2025-09-20 reproduction after reinstalling extras)
Suspected Cause: Smoke profile disables pytest plugin autoloading and now injects -p pytest_cov automatically, but pytest-bdd hooks are still skipped. When a test module calls pytest_bdd.scenarios the CONFIG_STACK is empty, leading to an IndexError.
Next Actions:
  - [ ] Ensure pytest-bdd is explicitly loaded when smoke mode sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 (either by injecting -p pytest_bdd or by loading scenarios via import hooks).
  - [ ] Add regression test that invokes the smoke profile in-process and asserts pytest-bdd scenario discovery succeeds without relying on plugin autoload.
  - [ ] Update docs/plan.md and docs/tasks.md with remediation guidance and link the new regression test.
  - [x] Capture failing smoke run output after reinstalling extras on 2025-09-20 and store the log under logs/run-tests-smoke-fast-20250920.log for reference during triage.
Resolution Evidence:
  - (pending)
