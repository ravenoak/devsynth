Title: Smoke run fails due to FastAPI/Starlette TestClient MRO regression
Date: 2025-09-21 05:29 UTC
Status: closed 2025-09-23 05:31 UTC
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
Exit Code: 1
Artifacts:
  - logs/run-tests-smoke-fast-20250921T052856Z.log (pre-fix failure)
  - logs/run-tests-smoke-fast-20250921T054207Z.log (pre-fix failure)
  - logs/run-tests-smoke-fast-20250921T160631Z.log (post-fix success)
  - logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log (post-lockfile verification)
Suspected Cause: After reinstalling extras on 2025-09-21 the environment resolved FastAPI 0.116.1 and Starlette 0.47.3. Starlette's 0.47 line introduces `starlette.websockets.WebSocketDisconnect` as a `typing.Protocol`. When FastAPI's TestClient imports Starlette's `WebSocketDenialResponse` helper, Python 3.12 cannot compose the method resolution order between the legacy object base class and the new protocol. The smoke profile now fails during collection before any tests run.
Next Actions:
  - [x] Pin Starlette to a compatible release (<=0.46.x) or apply FastAPI's compatibility patch once available.【F:pyproject.toml†L49-L51】【F:poetry.lock†L6722-L6737】
  - [x] Re-run `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and capture a green log.【F:logs/run-tests-smoke-fast-20250921T160631Z.log†L33-L40】
  - [x] Update docs/plan.md §Acceptance Criteria with the remediation and reclassify tasks 13.1/19.3 once the smoke suite passes again.【F:docs/plan.md†L39-L46】【F:docs/tasks.md†L131-L140】
  - [x] Cross-check other API behavior tests for compatibility regressions after adjusting dependencies (regression unit test guards the CLI path).【F:tests/unit/application/cli/test_run_tests_cmd_smoke.py†L1-L120】
  - [x] Document the follow-up smoke rerun (`logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log`) in release readiness notes and align docs/tasks.md §28 with the dependency pin rationale.【F:logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log†L1-L6】【F:docs/plan.md†L134-L195】【F:docs/tasks.md†L280-L286】
Resolution Evidence:
  - Starlette pinned `<0.47` with Poetry lock regenerated; FastAPI's TestClient now imports cleanly via the sitecustomize shim that rewrites `WebSocketDenialResponse`.【F:pyproject.toml†L49-L51】【F:poetry.lock†L6722-L6737】【F:src/sitecustomize.py†L12-L65】
  - Smoke CLI regression tests cover the new behavior, and the latest green run (2025-09-23) captures coverage diagnostics under `test_reports/coverage.json` while skipping enforcement in smoke mode.【F:tests/unit/application/cli/test_run_tests_cmd_smoke.py†L1-L142】【F:logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log†L1464-L1469】
  - 2025-10-20: Rebased on FastAPI 0.115.5/Starlette 0.41.3 per upstream release notes (Pydantic 2.10 support and `TestClient.raw_path` fix) and reran the smoke profile to capture `logs/run-tests-smoke-fast-20251020T171830Z.log`; the command still warns about skipped coverage artifacts but exits 0 for regression tracking.【F:pyproject.toml†L54-L55】【F:docs/release/0.1.0-alpha.1.md†L36-L41】【F:logs/run-tests-smoke-fast-20251020T171830Z.log†L1-L20】

Documentation traceability (2025-09-23):
  - Regression narrative, rerun evidence, and residual risk recorded in docs/plan.md §§Commands executed, Gaps, and Academic rigor.【F:docs/plan.md†L120-L198】
  - Research log summarizing FastAPI/Starlette Python 3.12 findings plus rerun transcript captured in docs/task_notes.md.【F:docs/task_notes.md†L208-L249】【F:docs/task_notes.md†L250-L271】
