Title: Smoke run fails due to FastAPI/Starlette TestClient MRO regression
Date: 2025-09-21 05:29 UTC
Status: open
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
Exit Code: 1
Artifacts:
  - logs/run-tests-smoke-fast-20250921T052856Z.log
  - logs/run-tests-smoke-fast-20250921T054207Z.log
Suspected Cause: After reinstalling extras on 2025-09-21 the environment resolved FastAPI 0.116.1 and Starlette 0.47.3. Starlette's 0.47 line introduces `starlette.websockets.WebSocketDisconnect` as a `typing.Protocol`. When FastAPI's TestClient imports Starlette's `WebSocketDenialResponse` helper, Python 3.12 cannot compose the method resolution order between the legacy object base class and the new protocol. The smoke profile now fails during collection before any tests run.
Next Actions:
  - [ ] Pin Starlette to a compatible release (<=0.37.x) or apply FastAPI's compatibility patch once available.
  - [ ] Re-run `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and capture a green log.
  - [ ] Update docs/plan.md §Acceptance Criteria with the remediation and reclassify tasks 13.1/19.3 once the smoke suite passes again.
  - [ ] Cross-check other API behavior tests for compatibility regressions after adjusting dependencies.
  - [ ] Document the follow-up smoke rerun (logs/run-tests-smoke-fast-20250921T054207Z.log) in release readiness notes and align docs/tasks.md §28 research with dependency pin recommendations.
Resolution Evidence:
  - Pending (smoke suite currently fails).
