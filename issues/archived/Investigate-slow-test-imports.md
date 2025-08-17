# Issue 144: Investigate slow test imports
Milestone: 0.1.0-alpha.1 (completed 2025-08-17)
Status: closed
Priority: medium
Dependencies: None

## Progress
- Audited tests for heavy optional dependencies.
- Guarded `faiss` import in `tests/unit/application/memory/test_faiss_store.py` with `pytest.importorskip`.
- Verified quick test startup with `poetry run devsynth run-tests --speed=fast`.

## References
- `poetry run devsynth run-tests --speed=fast`
- `poetry run pytest tests/unit --maxfail=1 -q`
