---
title: "DevSynth 0.1.0a1 — Current Actionable Tasks (Authoritative)"
date: "2025-10-26"
version: "0.1.0-alpha.1"
tags:
  - tasks
  - checklist
  - readiness
status: "in-progress"
author: "DevSynth Team"
source: "Aligned with docs/plan.md (Updated 2025-10-26)"
---

# DevSynth 0.1.0a1 — Current Actionable Tasks

Instructions
- Execute tasks top-to-bottom. Each task defines explicit acceptance criteria.
- Run all commands via Poetry to ensure plugins/extras and repo-local virtualenvs are honored.
- Artifacts must be written to test_reports/, htmlcov/, and diagnostics/ as specified.

1. [ ] Clean collection hygiene (no errors; large suite enumerates)
   Acceptance criteria:
   - `poetry run pytest --collect-only -q` completes without errors (exit code 0).
   - Save stdout to `diagnostics/pytest_collect_only_latest.log`.
   - A focused collector also succeeds: `poetry run pytest -k nothing --collect-only -q` → exit 0; log to `diagnostics/pytest_collect_only_k_nothing_latest.log`.

2. [ ] Smoke run is green and produces coverage data (autoload off)
   Acceptance criteria:
   - Command: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`.
   - Exit code 0; log saved to `test_reports/smoke_fast.log`.
   - `.coverage` file exists at repo root upon completion.
   - `test_reports/coverage.json` exists and contains `totals.percent_covered`.
   - If autoload is disabled, logs show injection of `-p pytest_cov` and `-p pytest_bdd.plugin`.

3. [ ] Optional backends universally gated (no import failures when extras absent)
   Acceptance criteria:
   - Behavior/integration suites import optional providers only behind `@pytest.mark.requires_resource("<NAME>")` and `pytest.importorskip`.
   - With all resource env vars unset (defaults), `poetry run pytest -k memory -q` shows skips (not errors) for CHROMADB/FAISS/KUZU/LMDB/etc.
   - Save summary to `diagnostics/optional_backend_gating_summary.txt`.

4. [ ] Exactly one speed marker per test function
   Acceptance criteria:
   - `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json` → 0 violations.
   - Commit the regenerated `test_markers_report.json` and `test_markers_current.json`.

5. [ ] Behavior assets valid (feature paths and step modules)
   Acceptance criteria:
   - No `FileNotFoundError` for BDD features; all loaders point into `tests/behavior/features/general/` (where applicable).
   - No `IndentationError`/`NameError` in behavior step modules.
   - Evidence: clean rerun of Task 1 logs plus a short targeted run `poetry run pytest tests/behavior -k nothing --collect-only -q` saved to `diagnostics/behavior_collect_only_latest.log`.

6. [ ] Strict typing is green at HEAD
   Acceptance criteria:
   - `poetry run mypy --strict src/devsynth` exits 0.
   - Save outputs to `diagnostics/mypy_strict_latest.txt` and `diagnostics/mypy_strict_manifest_latest.json` (if applicable).

7. [ ] Fast+medium aggregate ≥90% coverage with artifacts
   Acceptance criteria:
   - Command: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`.
   - Exit code 0 with gate PASS message or equivalent; overall `totals.percent_covered >= 90`.
   - Artifacts present: `.coverage`, `test_reports/coverage.json`, and HTML under `htmlcov/`.
   - Save CLI output to `artifacts/releases/0.1.0a1/fast-medium/latest/devsynth_run_tests_fast_medium.txt` and copy JSON/HTML into the same folder.
   - If collector instability occurs, repeat with segmentation: `--segment --segment-size=75`; acceptance remains ≥90% with combined artifacts.

8. [ ] CLI run-tests invariants honored (instrumentation, segmentation, inventory)
   Acceptance criteria:
   - Smoke logs show `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and plugin injection when needed; no IndexError from pytest-bdd discovery.
   - Inventory mode works: `poetry run devsynth run-tests --inventory` writes `test_reports/test_inventory.json` and exits.
   - Segmentation appends coverage across batches: `--segment --segment-size=75` still generates a single combined HTML/JSON artifact set.
   - Save a minimal transcript for each check under `diagnostics/cli_invariants/`.

9. [ ] Reports and inventory bundle exported
   Acceptance criteria:
   - `--report` writes an HTML report under `test_reports/` (pytest-html defaults) during Task 7 run.
   - `--inventory` exports `test_reports/test_inventory.json` and exits 0.
   - Include both files in the `artifacts/releases/0.1.0a1/fast-medium/latest/` bundle.

10. [ ] Documentation refreshed for maintainers
    Acceptance criteria:
    - docs/user_guides/cli_command_reference.md reflects smoke behavior (autoload off, plugin injection), coverage gate defaults, and segmentation usage.
    - README.md and/or docs mention provider defaults and resource flags per project guidelines.
    - A maintainer following docs can reproduce Tasks 1, 2, 6, and 7 on a clean workstation.

11. [ ] UAT bundle compiled
    Acceptance criteria:
    - Archive in `artifacts/releases/0.1.0a1/uat/` the following: Task 1–2 logs, strict mypy log (Task 6), coverage manifest and HTML (Task 7), and inventory/report outputs (Task 9).
    - Checklist in `issues/release-finalization-uat.md` updated with links to the above files and marked ready for maintainer sign-off.

12. [ ] CI posture maintained and post-tag PR prepared
    Acceptance criteria:
    - All `.github/workflows/*.yml` use only `workflow_dispatch` triggers pre-tag.
    - Draft PR exists to re-enable guarded triggers post-tag; include concurrency groups and artifact upload steps (test_reports/, htmlcov/, coverage.json, diagnostics/doctor_run.txt).
    - Evidence: link PR draft and confirm current workflows are dispatch-only.

13. [ ] Environment snapshot and reproducibility
    Acceptance criteria:
    - Capture: `poetry run python -V`, `poetry --version`, `poetry run pip freeze`, `poetry run devsynth doctor`, and UTC timestamp; store under `diagnostics/` with `*_latest.*` suffixes.
    - Rerunning Tasks 1–2 after a fresh shell continues to succeed without manual reinstallation steps.

Appendix: Authoritative commands (for repetition)
- Collect-only: `poetry run pytest --collect-only -q`
- Smoke: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- Aggregate: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`
- Segmented aggregate (fallback): `poetry run devsynth run-tests --speed=fast --speed=medium --segment --segment-size=75 --no-parallel --report`
- Typing: `poetry run mypy --strict src/devsynth`
- Markers check: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`
- Inventory only: `poetry run devsynth run-tests --inventory`
