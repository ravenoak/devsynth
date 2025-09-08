# Diagnostics and Environment Checks

This guide describes quick, repeatable checks to validate your local setup and ensure the test suite can be collected and executed as expected.

Related references:
- project guidelines (authoritative commands and conventions)
- docs/developer_guides/testing.md (test strategy and fixtures)
- docs/user_guides/cli_command_reference.md (CLI options)

## Quick Sanity

Use Poetry to guarantee the correct plugin surface and virtual environment.

- Collect tests only:
  - poetry run pytest --collect-only -q
- Run doctor:
  - poetry run devsynth doctor
- Fast unit run (no parallel, early stop):
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
- Smoke mode (reduced plugin surface):
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

## Diagnostics Command Flow Checklist

Use this flow when something goes wrong. It aligns with docs/plan.md and project guidelines.

1. Verify environment
   - poetry --version (ensure Poetry is installed)
   - python --version (expect Python 3.12.x)
   - poetry env info
2. Ensure dependencies are installed
   - poetry install --with dev --extras "tests retrieval chromadb api"
3. Collect-only to surface import errors quickly
   - poetry run pytest --collect-only -q
4. Run fast, smoke, no-parallel baseline (Task 1)
   - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
5. If failures persist, disable smoke (plugin surface on) but keep no-parallel
   - poetry run devsynth run-tests --speed=fast --no-parallel --maxfail=1
6. Try parallel to reveal xdist issues
   - poetry run devsynth run-tests --speed=fast
7. Check speed markers discipline
   - poetry run python scripts/verify_test_markers.py --changed
8. Inspect resource gating
   - Confirm DEVSYNTH_RESOURCE_* flags; enable only what you need
9. Generate HTML report for detailed review
   - poetry run devsynth run-tests --report
10. Capture rationale for non-trivial fixes
   - Append an entry to docs/rationales/test_fixes.md (thesis/antithesis/synthesis)

## Automated baseline check

We provide a helper script that automates the environment and baseline collection checks required by tasks 1 and 2 in docs/tasks.md.

Run it inside Poetry:

```bash
poetry run python scripts/diagnostics/check_env_and_collection.py
```

What it does:
- Verifies Python is 3.12.x
- Checks that Poetry is installed
- Provides install hints for the recommended setups
- Runs pytest collection and a minimal devsynth run-tests baseline

If it fails, follow the remediation tips printed at the end or refer to the testing guide.

## Security checks

For Task 29 (security and supply chain), use the provided script:

```bash
poetry run python scripts/run_security_checks.py
```

This runs:
- flake8 over src/ and tests/
- bandit over src/devsynth (excluding tests)
- safety with a full report

Address any HIGH/CRITICAL findings or document mitigations as needed.
