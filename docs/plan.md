# Improvement Plan

## Goal
Prepare DevSynth for the v0.1.0-alpha.1 release.

## Current Status
- Python 3.12 environment with Poetry-managed virtualenv.
- `go-task` installed; `task --version` returns 3.44.1.
- Fast tests succeed (162 passed, 27 skipped).
- `scripts/verify_test_markers.py` now scans changed files without marker issues.
- Medium test run surfaced numerous missing step definitions and a failing AST workflow test; suite still red.
- Specifications now contain "What proofs confirm the solution?" sections linked to BDD features.
- Release readiness remains blocked by failing medium tests and unverified slow tests.

## Next Steps
1. Follow the release checklist below to finalize environment setup.
2. Stub or implement missing BDD steps so medium suite completes.
3. After medium tests pass, execute slow suite and address remaining failures.

## Release Checklist
Refer to the [0.1.0-alpha.1 release guide](release/0.1.0-alpha.1.md) for detailed commands:

1. **Install go-task and verify tooling**
   ```bash
   bash scripts/install_dev.sh
   poetry env info --path
   task --version
   ```
2. **Install dependencies with development and test extras**
   ```bash
   poetry install --with dev --extras tests retrieval chromadb api
   ```
3. **Run repository checks**
   ```bash
   poetry run pre-commit run --files <changed>
   poetry run devsynth run-tests --speed=fast
   poetry run devsynth run-tests --speed=medium
   poetry run devsynth run-tests --speed=slow
   poetry run python tests/verify_test_organization.py
   poetry run python scripts/verify_test_markers.py
   poetry run python scripts/verify_requirements_traceability.py
   poetry run python scripts/verify_version_sync.py
   ```
4. **Validate deployment configuration**
   ```bash
   poetry run pytest tests/unit/deployment -m fast
   ```
5. **Prepare release artifacts and perform audit**
   ```bash
   task release:prep
   poetry run python scripts/verify_release_state.py
   ```
6. **Tag the release** only after resolving all entries in `dialectical_audit.log`.
