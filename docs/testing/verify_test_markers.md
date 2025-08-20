# Verifying test markers

DevSynth enforces speed markers on tests to keep runtimes predictable. The CI workflow
now runs `poetry run python scripts/verify_test_markers.py` to ensure each test is
marked appropriately.

## Local usage

Run the verification script before committing new or updated tests:

```bash
poetry run python scripts/verify_test_markers.py
```

The script fails if a test is missing a `fast`, `medium`, or `slow` marker or if
markers are misapplied.
