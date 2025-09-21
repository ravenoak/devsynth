Title: Smoke run fails due to FastAPI/Starlette TestClient MRO regression
Date: 2025-09-21 05:29 UTC
Status: resolved 2025-09-21 16:06 UTC
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
Exit Code: 1
Artifacts:
  - logs/run-tests-smoke-fast-20250921T052856Z.log (pre-fix failure)
  - logs/run-tests-smoke-fast-20250921T054207Z.log (pre-fix failure)
  - logs/run-tests-smoke-fast-20250921T160631Z.log (post-fix success)
Suspected Cause: After reinstalling extras on 2025-09-21 the environment resolved FastAPI 0.116.1 and Starlette 0.47.3. Starlette's 0.47 line introduces `starlette.websockets.WebSocketDisconnect` as a `typing.Protocol`. When FastAPI's TestClient imports Starlette's `WebSocketDenialResponse` helper, Python 3.12 cannot compose the method resolution order between the legacy object base class and the new protocol. The smoke profile now fails during collection before any tests run.
Next Actions:
  - [x] Pin Starlette to a compatible release (<=0.46.x) or apply FastAPI's compatibility patch once available.【F:pyproject.toml†L49-L51】【F:poetry.lock†L6722-L6737】
  - [x] Re-run `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and capture a green log.【F:logs/run-tests-smoke-fast-20250921T160631Z.log†L33-L40】
  - [x] Update docs/plan.md §Acceptance Criteria with the remediation and reclassify tasks 13.1/19.3 once the smoke suite passes again.【F:docs/plan.md†L39-L46】【F:docs/tasks.md†L131-L140】
  - [x] Cross-check other API behavior tests for compatibility regressions after adjusting dependencies (regression unit test guards the CLI path).【F:tests/unit/application/cli/test_run_tests_cmd_smoke.py†L1-L120】
  - [x] Document the follow-up smoke rerun (logs/run-tests-smoke-fast-20250921T160631Z.log) in release readiness notes and align docs/tasks.md §28 research with dependency pin recommendations.【F:docs/plan.md†L143-L151】【F:docs/tasks.md†L166-L173】
Resolution Evidence:
  - Starlette pinned `<0.47` with Poetry lock regenerated; FastAPI's TestClient now imports cleanly via the sitecustomize shim that rewrites `WebSocketDenialResponse`.【F:pyproject.toml†L49-L51】【F:poetry.lock†L6722-L6737】【F:src/sitecustomize.py†L12-L65】
  - Smoke CLI regression tests cover the new behavior, and the green run captures coverage artifacts for diagnostics under `test_reports/coverage.json`.【F:tests/unit/application/cli/test_run_tests_cmd_smoke.py†L1-L142】【F:logs/run-tests-smoke-fast-20250921T160631Z.log†L33-L40】
