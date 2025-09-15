# run-tests CLI stalls on networkx import
Milestone: 0.1.0a1
Status: open
Priority: high
Dependencies: poetry install --with dev --extras "tests retrieval chromadb api"

## Problem Statement
Invoking the test runner via `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` produces no output and never completes. The CLI also hangs when requesting help, blocking coverage generation.

## Action Plan
- [ ] Minimize startup imports to avoid networkx recursion.
- [ ] Provide a non-CLI fallback for running tests until the hang is resolved.
- [ ] Capture diagnostics to isolate the import loop.

## Progress
- 2025-09-15: Fresh environment prepared with `poetry install --with dev --extras "tests retrieval chromadb api"`; run-tests command hangs without output.
- 2025-09-15: `poetry run devsynth --help` terminated with `KeyboardInterrupt` while importing `networkx`.

## References
- `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`
- `poetry run devsynth --help`
