# AGENTS.md

## Project Snapshot

**What is DevSynth?**
DevSynth implements agent services under `src/devsynth/` and supporting scripts under `scripts/`. It values clarity, collaboration, and dependable automation. For architecture and policy references, see `docs/` and `CONTRIBUTING.md`.

## Setup

**How do I prepare my environment?**
1. Ensure Python 3.12 is active and Poetry created a virtual environment (enforced via the committed `poetry.toml`):
   ```bash
   python --version
   poetry env info --path
   ```
   If `poetry env info --path` prints nothing or points elsewhere, recreate the environment:
   ```bash
   poetry env use 3.12 && poetry install --with dev --extras tests retrieval chromadb api
   ```
2. Provision the environment:
   ```bash
   bash scripts/install_dev.sh      # general setup (installs Taskfile if needed)
   bash scripts/codex_setup.sh      # Codex agents
   task --version                   # verify Taskfile is available
   ```
3. Install dependencies with development and test extras and run commands through `poetry run`.

## Testing

**How do I keep the build green?**
Codex-style agents run commands iteratively until all tests pass:
```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<fast|medium|slow>
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```
CI runs `poetry run python scripts/verify_test_markers.py` to ensure each test carries a speed marker.
`tests/conftest.py` provides an autouse `global_test_isolation` fixture; avoid setting environment variables at import time. Use speed markers `fast`, `medium`, or `slow` from `tests/conftest_extensions.py` and combine them with context markers when needed. Optional services should be guarded with environment variables like `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` or `pytest.importorskip`.

## Conventions

**What practices guide contributions?**
- Begin with the Socratic checklist: *What is the problem?* and *What proofs confirm the solution?*
- Follow the specification-first BDD workflow: draft specs in `docs/specifications/` and pair them with failing features under `tests/behavior/features/` before implementation.
- Use [Conventional Commits](https://www.conventionalcommits.org/) with a one-line summary and descriptive body, then open a pull request with `make_pr` that summarizes changes and test evidence.
- Honor all policies under `docs/policies/` (security, audit, etc.), including the [Dialectical Audit Policy](docs/policies/dialectical_audit.md); resolve `dialectical_audit.log` before submission.
- Use the in-repo issue tracker (`issues/`; see `issues/README.md`).
- Consult `docs/release/0.1.0-alpha.1.md` for release steps and `.github/workflows/` for automation guidelines.

## Further Reading

**Where can I learn more?**
- Detailed API conventions: `docs/api_reference.md`
- Additional architecture and policy guides: `docs/`
- Contribution guidelines: `CONTRIBUTING.md`

## AGENTS.md Compliance

**What is the scope of these instructions?**
They apply to the entire repository and follow the OpenAI Codex AGENTS.md spec (repo-wide scope; nested AGENTS files override). Update AGENTS files whenever workflows change.
