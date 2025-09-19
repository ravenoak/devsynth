Title: Release finalization for 0.1.0a1
Date: 2025-09-13 00:00 UTC
Status: open
Affected Area: release
Reproduction:
  - N/A (planning issue)
Exit Code: N/A
Artifacts:
  - docs/coverage.svg
  - htmlcov/ (omitted from commit; exceeds Codex diff size)
  - coverage.json (omitted from commit; exceeds Codex diff size)
Suspected Cause: Pending release tasks before tagging v0.1.0a1.
Next Actions:
  - [x] Draft release notes and update CHANGELOG.md.
  - [x] Perform final full fast+medium coverage run and archive artifacts. Coverage artifacts not committed due to Codex diff size limits.
  - [ ] Complete User Acceptance Testing with stakeholder sign-off.
  - [ ] Maintainers tag v0.1.0a1 on GitHub once all tasks complete.
Progress:
- 2025-09-13: Plan and tasks updated to clarify manual GitHub tagging after UAT.
- 2025-09-13: Environment bootstrapped; smoke tests and verification scripts pass after reinstalling dependencies.
- 2025-09-13: Release notes drafted and CHANGELOG updated.
- 2025-09-13: Re-ran smoke tests and verification scripts; full coverage run attempted but timed out. Opened issues/strict-typing-roadmap.md to consolidate remaining typing tasks.
- 2025-09-13: Final fast+medium coverage run attempted; run reported `ERROR tests/unit/general/test_test_first_metrics.py`. Coverage artifacts omitted from commit due to Codex diff size limits.
- 2025-09-13: Verified fresh environment with `poetry install`; smoke tests and verification scripts passed; awaiting UAT and maintainer tagging.
- 2025-09-13: Fixed path handling for `test_first_metrics` and reran coverage; committed updated reports.
- 2025-09-15: Reinstalled go-task, executed smoke tests and verification scripts; awaiting UAT and maintainer tagging.
- 2025-09-15: Reinstalled dependencies and reran smoke/verification scripts; UAT and tagging pending.
- 2025-09-15: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report --maxfail=1` succeeded but coverage stayed at 13.68 % with empty HTML output; coverage remediation reopened (see docs/tasks.md §21 and issues/coverage-below-threshold.md).
- 2025-09-15: Smoke profile run after reinstalling `devsynth` (`poetry install --with dev --all-extras`) emitted coverage warning (`totals.percent_covered` missing) and wrote empty coverage artifacts, confirming instrumentation gaps remain before UAT can proceed.
- 2025-09-16: Full reinstall plus smoke and fast+medium runs reproduced the coverage warning and left `.coverage` missing; gating cannot proceed until instrumentation writes real totals (`poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`, `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report --maxfail=1`).【63011a†L1-L4】【50195f†L1-L5】
- 2025-09-17: Repeated smoke and fast+medium commands exit with "Coverage artifact generation skipped" and code 1 because `.coverage` is absent; last captured coverage JSON before cleanup reported only 20.78 %, so coverage remediation remains a release blocker.【d5fad8†L1-L4】【20dbec†L1-L5】【45de43†L1-L2】【cbc560†L1-L3】
- 2025-09-17: Promoted the `devsynth run-tests`, `finalize dialectical reasoning`, and `WebUI integration` specifications to review with cross-referenced BDD, unit, and property coverage so UAT can trace acceptance evidence directly to automated suites.【F:docs/specifications/devsynth-run-tests-command.md†L1-L39】【F:docs/specifications/finalize-dialectical-reasoning.md†L1-L80】【F:docs/specifications/webui-integration.md†L1-L57】【F:tests/behavior/features/devsynth_run_tests_command.feature†L1-L23】【F:tests/behavior/features/finalize_dialectical_reasoning.feature†L1-L15】【F:tests/behavior/features/general/webui_integration.feature†L1-L52】【F:tests/unit/application/cli/commands/test_run_tests_features.py†L1-L38】【F:tests/unit/methodology/edrr/test_reasoning_loop_invariants.py†L1-L200】【F:tests/unit/interface/test_webui_handle_command_errors.py†L1-L109】【F:tests/property/test_run_tests_sanitize_properties.py†L1-L37】【F:tests/property/test_reasoning_loop_properties.py†L1-L200】【F:tests/property/test_webui_properties.py†L1-L44】
- 2025-09-19: Bootstrap script converted Poetry to `/workspace/devsynth/.venv`, but smoke and fast+medium CLI profiles still skip coverage artifacts (`Coverage artifact generation skipped: data file missing`), keeping the ≥90 % gate and UAT sign-off blocked.【b60531†L1-L1】【21111e†L1-L2】【060b36†L1-L5】【eb7b9a†L1-L5】【f1a97b†L1-L3】
Resolution Evidence:
  - docs/tasks.md item 19
