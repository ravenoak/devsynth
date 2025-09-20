Title: Smoke run fails when pytest-bdd config not loaded
Date: 2025-09-20 14:47 UTC
Status: resolved
Affected Area: tests
Reproduction:
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
Exit Code: 1
Artifacts:
  - logs/run-tests-smoke-fast-20250920.log
  - logs/run-tests-smoke-fast-20250920T000000Z.log (2025-09-20 reproduction after reinstalling extras)
  - logs/run-tests-smoke-fast-20250920T1721Z.log (post-fix run showing pytest-bdd loads and the suite reaches a FastAPI TestClient MRO failure)
Suspected Cause: Smoke mode previously disabled plugin autoloading without reloading pytest-bdd, leaving `CONFIG_STACK` empty and causing an IndexError during scenario collection. Injecting `-p pytest_bdd.plugin` alongside pytest-cov restores the hook; the remaining failure is unrelated (FastAPI TestClient MRO regression tracked separately).
Next Actions:
  - [x] Ensure pytest-bdd is explicitly loaded when smoke mode sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 (inject `-p pytest_bdd.plugin` via CLI and shared test runner).
  - [x] Add regression test that invokes the smoke profile in-process and asserts pytest-bdd scenario discovery succeeds without relying on plugin autoload.
  - [x] Update docs/plan.md and docs/tasks.md with remediation guidance and link the new regression test.
  - [x] Capture failing smoke run output after reinstalling extras on 2025-09-20 and store the log under logs/run-tests-smoke-fast-20250920.log for reference during triage.
Resolution Evidence:
  - CLI and shared runner now append `-p pytest_bdd.plugin` whenever `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, keeping pytest-bdd active alongside pytest-cov during smoke runs.【F:src/devsynth/testing/run_tests.py†L343-L370】【F:src/devsynth/application/cli/commands/run_tests_cmd.py†L337-L356】
  - In-process Typer regression `test_smoke_command_injects_pytest_bdd_plugin` confirms the smoke profile completes without the previous IndexError and produces coverage artifacts even with plugin autoloading disabled.【F:tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py†L126-L160】
  - docs/plan.md §21 and docs/tasks.md §21.12 summarize the remediation and link the new log artifact `logs/run-tests-smoke-fast-20250920T1721Z.log` for traceability.【F:docs/plan.md†L46-L58】【F:docs/plan.md†L196-L204】【F:docs/tasks.md†L205-L222】【F:logs/run-tests-smoke-fast-20250920T1721Z.log†L1-L46】
