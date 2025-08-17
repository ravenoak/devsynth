# Investigate slow test imports
Milestone: 0.1.0-alpha.1
Status: open
Priority: medium
Dependencies: None

## Progress
- Running any test or `devsynth run-tests` hangs during module import.
- Initial investigation shows heavy optional dependencies delaying startup.

## References
- `poetry run devsynth run-tests --speed=fast`
- `poetry run pytest tests/unit --maxfail=1 -q`
