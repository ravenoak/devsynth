# AGENTS.md

## Project Snapshot

**What is DevSynth?**
DevSynth implements agent services under `src/devsynth/` and supporting scripts under `scripts/`. It values clarity, collaboration, and dependable automation. For architecture and policy references, see `docs/` and `CONTRIBUTING.md`.

> **NOTE:** All GitHub Actions workflows are temporarily disabled and must be triggered manually via `workflow_dispatch` until the `v0.1.0a1` tag is created (see `docs/tasks.md` item 10.1). No `push`, `pull_request`, or `schedule` triggers may be added during this period. The CI workflow provides smoke, unit+integration, and typing+lint jobs with concurrency controls and caches for Poetry, pip, and `.pytest_cache`; on failures it uploads `test_reports/`, `htmlcov/`, `coverage.json`, and `diagnostics/doctor_run.txt`.

## Setup

**How do I prepare my environment?**
1. Ensure Python 3.12 is active and Poetry created a virtual environment (enforced via the committed `poetry.toml`):
   ```bash
   python --version
   poetry env info --path  # must print the virtualenv path
   ```
   If `poetry env info --path` prints nothing or points elsewhere, recreate the environment:
   ```bash
   poetry env use 3.12 && poetry install --with dev --extras tests retrieval chromadb api
   ```
2. Provision the environment:
   ```bash
   bash scripts/install_dev.sh      # general setup (auto-installs go-task)
   bash scripts/codex_setup.sh      # Codex agents (finishes <15m, warns >10m)
   task --version                   # verify Taskfile is available
   ```
   The install script downloads `go-task` to `$HOME/.local/bin` and adds it to
   the `PATH` for subsequent steps. These checks are mirrored in
   [scripts/install_dev.sh](scripts/install_dev.sh),
   the release guide [docs/release/0.1.0-alpha.1.md](docs/release/0.1.0-alpha.1.md),
   and the CI workflow [.github/workflows/ci.yml](.github/workflows/ci.yml).
   - Always inspect `scripts/codex_setup.sh` and `scripts/codex_maintenance.sh`
     first when diagnosing environment failures. Provisioning calls them as
     `scripts/codex_setup.sh || touch CODEX_ENVIRONMENT_SETUP_FAILED` for new
     containers and `scripts/codex_maintenance.sh || touch
     CODEX_ENVIRONMENT_MAINTENANCE_FAILED` for cached resumes. Both scripts now
     self-install Poetry via `pipx` when missing, enforce Poetry 2.2.1 (to match
     the lock file), normalize the project version from either `[tool.poetry]`
     or `[project]`, and run `poetry check` up front so lock-file drift is
     reported immediately.
   - On a cached container rerun the lighter maintenance script directly to
     resync dependencies and run fast health probes:
     ```bash
     bash scripts/codex_maintenance.sh
     ```
     Successful runs remove the corresponding `CODEX_ENVIRONMENT_*_FAILED`
     marker files so the workspace reflects its current status.
3. Install dependencies with development and test extras. Use `poetry run` for all Python invocations (or `task` for Taskfile targets) so commands run inside the Poetry-managed virtualenv.

   Optional test extras map to resource markers:
   - `poetry install --extras retrieval` provides `kuzu` and `faiss-cpu` for tests marked with `requires_resource("kuzu")` or `requires_resource("lmdb")`.
   - `poetry install --extras chromadb` enables ChromaDB-specific tests marked `requires_resource("chromadb")`.
   - `poetry install --extras memory` pulls the full memory stack if running all back-end tests.

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
- Use system time when recording the current date or datetime.
- Honor all policies under `docs/policies/` (security, audit, etc.), including the [Dialectical Audit Policy](docs/policies/dialectical_audit.md); resolve `dialectical_audit.log` before submission.
- Use the in-repo issue tracker (`issues/`; see `issues/README.md`).
- Consult `docs/release/0.1.0-alpha.1.md` for release steps and `.github/workflows/` for automation guidelines.

## Directory-Specific Guidance

**What additional guidance applies to specific directories?**

### Source Code (`src/devsynth/`)
- Follow the specification-first BDD workflow: draft specs in `docs/specifications/` and failing features in `tests/behavior/features/` before writing code
- Adhere to the [Security Policy](docs/policies/security.md) and [Dialectical Audit Policy](docs/policies/dialectical_audit.md)
- All source changes should be accompanied by appropriate tests

### Testing (`tests/`)
- Each test must include exactly one speed marker (`fast`, `medium`, `slow`) from `tests/conftest_extensions.py`
- Guard optional services with `pytest.importorskip` and environment variables like `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE`
- The `tests/conftest.py` provides an autouse `global_test_isolation` fixture; avoid setting environment variables at import time
- Agent API tests require the `api` extra: `poetry install --extras api`

### Documentation (`docs/`)
- Follow [Documentation Policies](docs/policies/documentation_policies.md) for style and structure
- Capture new requirements in `docs/specifications/` before implementation
- Honor the [Dialectical Audit Policy](docs/policies/dialectical_audit.md) and resolve `dialectical_audit.log`
- Use system time when recording current date or datetime

## Further Reading

**Where can I learn more?**
- Detailed API conventions: `docs/api_reference.md`
- Additional architecture and policy guides: `docs/`
- Contribution guidelines: `CONTRIBUTING.md`

## IDE Integration

**DevSynth works with any modern IDE or code editor.** While the project includes a `.cursor/` directory for users who prefer Cursor IDE, DevSynth itself is IDE-agnostic and focuses on agent orchestration and structured development methodologies.

### Development Workflow Integration
1. **EDRR-Enhanced Development**: Follow the Expand-Differentiate-Refine-Retrospect framework for systematic development
2. **Specification-Driven Coding**: Use SDD workflow (Specify, Plan, Tasks, Implement) regardless of IDE
3. **Multi-Agent Coordination**: Leverage DevSynth's agent orchestration capabilities
### Recommended IDE Setup
Use any IDE that supports:
- Python development
- Poetry environment management
- Git integration
- Testing frameworks (pytest)

## AGENTS.md Compliance

**What is the scope of these instructions?**
They apply to the entire repository and follow the OpenAI Codex AGENTS.md spec (repo-wide scope; nested AGENTS files override). Update AGENTS files whenever workflows change.
