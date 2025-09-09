# Pull Request

Thank you for contributing to DevSynth! Please fill out the checklist below to help us maintain determinism, clarity, and safety per .junie/guidelines.md and docs/plan.md.

## Summary
- What does this change do in one or two sentences?
- Linked issues or tasks: e.g., fixes #123; addresses docs/tasks.md items: [ ]  …

## Scope of Change
- [ ] Code
- [ ] Tests
- [ ] Docs
- [ ] CI/Tooling
- [ ] Other: ____________

## Socratic Checklist
- Assumptions tested: What assumptions did you make? How did you test them?
- Hidden dependencies: What external systems, environment variables, files, or global state does this depend on?
- Minimal reproducible example (MRE): What is the smallest way to reproduce the observed bug/behavior?
- Failure modes: What can go wrong? How is it handled or made visible to users/devs?
- Rollback plan: If this has to be reverted, are follow-ups needed?

## Determinism and Test Discipline
- [ ] Exactly one speed marker per new/changed test (@pytest.mark.fast|medium|slow)
- [ ] Respect default marker filter (not memory_intensive) or use @pytest.mark.memory_intensive when appropriate
- [ ] Deterministic seeding (random, numpy) via fixtures or explicit seeds
- [ ] No real network calls unless explicitly gated (disable_network used; requires_resource flags applied)
- [ ] Timeouts applied where appropriate (enforce_test_timeout fixture or explicit)
- [ ] Writes constrained to tmp paths; no persistent side effects

## Resource Gating and Providers
- [ ] If optional backends are used (CHROMADB/DUCKDB/FAISS/KUZU/LMDB/RDFLIB/TINYDB), guarded by @pytest.mark.requires_resource and docs list how to enable locally
- [ ] LLM provider calls stubbed/offline by default; opt-in flags documented (DEVSYNTH_PROVIDER=stub by default in tests)

## CLI and Docs Consistency
- [ ] Commands in docs/examples use Poetry (poetry run …) per guidelines
- [ ] run-tests CLI options and examples align with docs/user_guides/cli_command_reference.md

## Acceptance Criteria (Release Readiness)
- [ ] Marker discipline passes for changed files (files_with_issues=0 for modified subset)
- [ ] Coverage meets or exceeds policy when strict gating is enabled (DEVSYNTH_STRICT_COVERAGE=1 with DEVSYNTH_COV_FAIL_UNDER=90)
- [ ] `poetry run devsynth doctor` passes in the applicable profile (no ModuleNotFoundError for webui when expected)
- [ ] Lint/type/security gates pass for changed files (black, isort, flake8, mypy, bandit, safety as applicable)

## Local Verification
Provide minimal commands used to validate:
```bash
poetry run pytest --collect-only -q
poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
poetry run python scripts/verify_test_markers.py --changed
```

## Pre-submit Checks
- [ ] PR is linked to related issues/tickets via GitHub "Linked issues" (required)
- [ ] scripts/verify_test_markers.py --changed passes with 0 issues on modified tests
- [ ] Exactly one speed marker per test function is present in all modified/added tests (@pytest.mark.fast|@pytest.mark.medium|@pytest.mark.slow)

## Screenshots / Logs (if applicable)
- Attach or paste relevant output.

## Notes
- Additional context, trade-offs, or follow-ups.
