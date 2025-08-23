# AGENTS.md

## Project Snapshot

**What is in this directory?**
This directory contains the DevSynth test suite.

## Setup

**How do I prepare for testing?**
Follow the repository setup from the root AGENTS and ensure all commands run through `poetry run`.
Agent API tests require the `api` extra.

## Testing

**How do I run tests?**
Run these commands iteratively until they pass:
```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<fast|medium|slow>
poetry run python scripts/verify_test_markers.py
```

## Conventions

**What testing conventions apply?**
- `tests/conftest.py` defines an autouse `global_test_isolation` fixture; avoid setting environment variables at import time.
- Each test includes exactly one speed marker (`fast`, `medium`, `slow`) from `tests/conftest_extensions.py`; combine with context markers when needed.
- Guard optional services with `pytest.importorskip` and env vars like `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE`.
- Keep commit messages Conventional and follow root AGENTS guidance for pull‑request workflow.

## Further Reading

**Where can I find more testing guidance?**
See additional policies under `../docs/policies/`.

## AGENTS.md Compliance

**What is the scope?**
These instructions apply to `tests/` and its subdirectories. Nested AGENTS files override these instructions.
