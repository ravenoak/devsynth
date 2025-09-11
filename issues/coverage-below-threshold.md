# Coverage below threshold

## Summary
Coverage run using `DEVSYNTH_PROPERTY_TESTING=true poetry run pytest --cov=src/devsynth --cov-report=term --cov-report=html -q` fails with numerous test failures, preventing generation of a complete coverage report and verifying the ≥90% requirement.

## Steps to Reproduce
1. Ensure dependencies installed via `poetry install --with dev --all-extras`.
2. Execute the coverage command above.

## Expected Behavior
Coverage report completes with ≥90% coverage.

## Actual Behavior
Test execution halts early due to failing tests, and coverage percentage cannot be determined.

## Notes
- Tasks `docs/tasks.md` items 13.3 and 13.4 remain unchecked pending resolution.
- Address flake8 lint failures, as they may contribute to test instability.
- 2025-09-11: `poetry run pytest -q --cov-fail-under=90 -k "nonexistent_to_force_no_tests"` fails during test collection due to missing modules `faiss` and `chromadb`; coverage remains unverified.
- 2025-09-19: `devsynth` installed; smoke and property tests pass. Full coverage run not executed this iteration; threshold remains unverified.
- 2025-09-27: Segmented coverage run executed for fast and medium tests, combined via `coverage combine`; HTML and JSON reports archived outside version control (`coverage-artifacts.tar.gz`). Threshold still unverified.
- 2025-09-28: Combined report `coverage report --fail-under=90` returned 5% total coverage, confirming the ≥90% requirement is unmet.
