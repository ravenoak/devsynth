# DevSynth 0.1.0a1 Testing & Release Readiness — Actionable Tasks Checklist (2025-09-01)

Note: Every task is actionable, ordered for execution, and starts with a checkbox. Follow the Maintainer Must‑Run Sequence after completing core remediation to validate outcomes. Reference lines from docs/plan.md are provided where helpful.

Environment Sanity Snapshot (2025-09-01 22:43 local)
- Verified toolchain availability during this session:
  - Poetry 2.1.4, pytest 8.4.1, mypy 1.17.1, flake8 7.3.0, black 25.1.0, isort 6.0.1, bandit 1.8.6, safety 3.2.3, curl 8.7.1, devsynth 0.1.0a1
  - lms CLI present; LM Studio endpoint reachable at http://127.0.0.1:1234 (GET /v1/models succeeded)
- This snapshot is informational and does not mark any checklist item complete; maintainers should still execute and capture evidence per Sections 2–3 and 11.

1. [x] Establish Maintainer Environment Baseline (docs/plan.md §3, lines 48–66)
   - [x] Use Python 3.12.x; ensure Poetry installed.
   - [x] Run: poetry install --with dev --extras "tests retrieval chromadb api llm memory lmstudio"
   - [x] Explicitly export baseline env vars in shell profile or session:
         DEVSYNTH_OFFLINE=true; DEVSYNTH_PROVIDER=stub; OPENAI_API_KEY=test-openai-key;
         DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false; DEVSYNTH_RESOURCE_CLI_AVAILABLE=true;
         DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true; LM_STUDIO_ENDPOINT=http://127.0.0.1:1234

2. [x] Verify Tooling Availability and Capture Diagnostics (plan §3a, lines 69–90)
   - [x] Capture versions for poetry, python, pip, pytest, mypy, flake8, black, isort, bandit, safety, curl, devsynth, task into diagnostics/*.txt as outlined.
   - [x] For LM Studio (only when live tests are planned): curl ${LM_STUDIO_ENDPOINT}/v1/models and save to diagnostics/lmstudio_models.json; note reachability.

3. [x] Add Evidence Capture Protocol (plan §7, lines 204–213)
  - [x] Ensure diagnostics/exec_log.txt is appended for each significant run with timestamp, command, exit code, artifacts, notes.
  - [x] Add a small helper script or Taskfile target to append these entries consistently (optional but recommended).

4. [x] Enforce Speed Marker Discipline Continuously (plan §2, §6.B, lines 40–46, 169–172)
  - [x] Ensure scripts/verify_test_markers.py runs locally: poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
  - [x] Add/confirm Taskfile target verify:markers that shells the above and fails on violations.
  - [x] Integrate into pre-commit (if not present): run marker verification on changed tests; fail commit on violations.

5. [x] Prevent Heavy Optional Imports in doctor/tests Paths (plan §6.C, lines 173–176)
   - [x] Audit devsynth doctor and devsynth run-tests code paths for imports of GUI/webui (streamlit/nicegui etc.).
   - [x] Refactor/confirm lazy-loading of optional UI modules behind feature flags/extras; avoid import at CLI startup and doctor path.
   - [x] Add tests to ensure doctor command does not import UI modules by default (guard regression).
   - [x] Re-run: poetry run devsynth doctor | tee diagnostics/doctor.txt (should not error on missing UI deps).

6. [x] Behavior Test Plugin Stability and Smoke Mode Guidance (plan §4.D, §6.D, lines 113–118, 177–179)
   - [x] Document in docs/developer_guides/testing.md when to use --smoke and typical plugin issues.
   - [x] If persistent plugin issues, identify via PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; selectively re-enable needed plugins only.
   - [x] Optionally add Taskfile target tests:behavior-fast-smoke if missing.

7. [x] Provider Configuration Defaults and Tests (plan §6.E, lines 180–182)
   - [x] Verify ProviderEnv.with_test_defaults() sets DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true when unset.
   - [x] Add or update unit tests asserting these defaults are applied by run-tests command.

8. [x] Property Tests Hygiene (plan §4.E, §6.F, lines 119–122, 183–185)
   - [x] Ensure all tests under tests/property/ include both @pytest.mark.property and exactly one speed marker.
   - [x] Update marker verification script scope if needed to include property tests.
   - [x] Document how to enable property tests: export DEVSYNTH_PROPERTY_TESTING=true; poetry run pytest tests/property/ -q

9. [x] Stabilize LM Studio Integration Tests (plan §6.A, §16, lines 162–168, 326–335)
   - [x] Implement lightweight health check in LM Studio provider/tests: GET ${LM_STUDIO_ENDPOINT}/v1/models; skip fast with clear reason if unreachable even when DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true.
   - [x] Add bounded retry/backoff (<= 5s total) for initial handshake calls in src/devsynth/application/llm/lmstudio_provider.py (or adapter used by tests only). Keep retries off for unit tests unless requires_resource('lmstudio').
   - [x] Add focused subset command to docs and Taskfile for lmstudio-only fast tests.
   - [x] Capture flake rate and outcomes under diagnostics/; open/close issues accordingly.

10. [x] Offline/Stub and Live Resource-Gated Runs (plan §4.F, lines 123–135)
    - [x] Validate offline/stub run excludes resource tests:
          poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai') and not requires_resource('lmstudio')" --no-parallel --maxfail=1
    - [ ] Live OpenAI subset: export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true and a real OPENAI_API_KEY; run the fast subset; capture diagnostics.
    - [ ] Live LM Studio subset: export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true; verify endpoint; run fast subset; capture diagnostics.

11. [x] Unit, Integration, Behavior Test Passes (plan §4 A–D, lines 94–118)
    - [x] Collection and inventory: poetry run pytest --collect-only -q; poetry run devsynth run-tests --inventory
    - [x] Unit fast: devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
    - [x] Integration fast: devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 (use --segment if needed)
    - [x] Behavior fast: devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1 (use --smoke if plugin issues)

12. [ ] Quality Gates: Format, Lint, Security, Typing (plan §4.H, lines 140–148)
    - [ ] black/isort/flake8 clean: poetry run black --check . && poetry run isort --check-only . && poetry run flake8 src/ tests/
    - [ ] bandit and safety clean: poetry run bandit -r src/devsynth -x tests && poetry run safety check --full-report
    - [ ] mypy strict passes: poetry run mypy src/devsynth
    - [ ] For modules with relaxations, add TODOs and tracking issue(s) to restore by 2025‑10‑01 per pyproject [tool.mypy] overrides.

13. [x] Requirements Traceability and Test Inventory (plan §6.H, lines 190–192)
    - [x] Ensure tests’ docstrings contain "ReqID:" tags; update missing ones.
    - [x] Run inventory and attach artifacts to release notes: poetry run devsynth run-tests --inventory | tee diagnostics/test_inventory_capture.txt

14. [x] Reports Generation (plan §4.G, lines 136–139)
    - [x] Produce HTML test report: poetry run devsynth run-tests --report --speed=fast --no-parallel | tee diagnostics/test_report_fast.txt

15. [x] Troubleshooting Quick Path (plan §4.I, §14–15, lines 149–152, 305–325)
    - [x] When failures occur, re-run smoke fast: devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 | tee diagnostics/fast_smoke_run.txt
    - [x] Use segmentation for instability: add --segment --segment-size 50
    - [x] Capture pytest version, pip list, UTC timestamp in diagnostics; minimize plugin surface via PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 when needed.
    - [x] File/update issues with reproduction commands and artifacts.

16. [x] Minimal CI Workflow (Post‑release Enablement) (plan §6.I, lines 193–201)
    - [x] Create a GitHub Actions workflow (disabled by default) with:
         - Ubuntu + Python 3.12
         - poetry install --with dev --extras "tests api llm"
         - devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
         - marker verification, mypy, flake8
         - caches for Poetry and pytest
    - [x] Set triggers to workflow_dispatch and nightly schedule only; keep disabled until post‑release.

17. [x] Update Documentation (Cross-cutting)
    - [x] Update docs/developer_guides/testing.md and docs/user_guides/cli_command_reference.md to reflect run recipes, smoke mode, segmentation, and resource-gated guidance.
    - [x] Ensure README.md references the Maintainer Must‑Run Sequence and links to test markers report and diagnostics guidance.

18. [x] Provider Modules: File-level Actions (plan §16, lines 326–335)
    - [x] src/devsynth/application/llm/lmstudio_provider.py: add health check helper and bounded retry/backoff wrapper for initial handshake; introduce LMStudioConnectionError/ModelError handling if not present; ensure tests can stub.
    - [x] src/devsynth/application/llm/provider_factory.py and src/devsynth/application/llm/providers.py: ensure lmstudio feature flag gating and selection logic is robust; add unit tests for provider selection based on env flags.
    - [x] tests/fixtures/lmstudio_service.py: add/prep fixtures to simulate transient failures and validate retry/backoff.

19. [x] Pre-commit and Taskfile Hygiene
  - [x] pre-commit: include hooks for black, isort, flake8, mypy, marker verification, and optionally bandit (advisory).
  - [x] Taskfile.yml: confirm targets exist — tests:unit-fast, tests:integration-fast, tests:behavior-fast-smoke, verify:markers, guardrails:all, doctor:lmstudio; add missing ones.

20. [ ] Exit Criteria Verification (plan §11, lines 237–248; §13 mapping)
    - [ ] Confirm each exit criterion with its command and record artifacts:
         unit/integration/behavior fast green; markers pass; offline stub excludes resources;
         live OpenAI and LM Studio subsets pass; type/lint/security gates green;
         evidence captured; release notes include test inventory and known limitations.

21. [ ] Rollout Schedule Compliance (plan §8, lines 214–219)
    - [ ] T+0: Execute §4 A–D and H; capture evidence; file/close issues for identified instabilities.
    - [ ] T+1: Complete §6 A–G; repeat core runs; generate report.
    - [ ] T+2: Freeze and tag 0.1.0a1; keep CI disabled until post‑release; then enable Minimal CI.

22. [x] Issues Review Protocol (plan §18, lines 345–349)
    - [x] Enumerate issues/ and link tickets within commits related to fixes.
    - [x] For non‑green runs, create/update an issue with reproduction, exit code, diagnostics paths, and suspected root cause.
    - [x] Close issues only after a green re‑run with artifacts attached.

23. [x] Maintainer Must‑Run Sequence (plan §19, lines 350–360)
    - [x] Wrapper target available: task maintainer:must-run (executes steps 1–10 with evidence capture to diagnostics/ and test_reports/)
    - [x] Run, in order:
         1) poetry install --with dev --extras "tests retrieval chromadb api llm memory lmstudio"
         2) task tests:collect && task verify:markers
         3) task tests:unit-fast
         4) task tests:integration-fast
         5) poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1
         6) poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai') and not requires_resource('lmstudio')" --no-parallel --maxfail=1
         7) Live OpenAI (opt‑in) fast subset
         8) Live LM Studio (opt‑in) fast subset (+ task doctor:lmstudio)
         9) Reports: --report
        10) Guardrails: task guardrails:all
