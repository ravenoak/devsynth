---
description: Core project philosophy, setup, and development workflow for DevSynth
globs:
  - "**/*"
alwaysApply: true
---

# DevSynth Core Development Rules

## Project Philosophy

DevSynth values **clarity**, **collaboration**, and **dependable automation**. All development follows a multi-disciplined approach driven by:

- **Dialectical reasoning**: thesis → antithesis → synthesis
- **Socratic method**: What is the problem? What proofs confirm the solution?
- **Systems thinking**: Understanding interconnections and emergent properties
- **Holistic perspective**: Considering the entire system context

## Environment Requirements

- **Python**: 3.12 only (`>=3.12,<3.13`)
- **Package Manager**: Poetry (use `poetry run` for all Python commands)
- **Task Runner**: go-task (use `task` for Taskfile targets)
- **Virtual Environment**: Poetry-managed (enforced via `poetry.toml`)

### Setup Verification

```bash
python --version              # Must show 3.12.x
poetry env info --path        # Must print virtualenv path
task --version                # Verify task runner available
poetry run devsynth --help    # Confirm DevSynth CLI works
```

## Critical Workflow: Specification-First BDD

**ALWAYS** follow this sequence (non-negotiable):

1. **Draft specification** in `docs/specifications/` answering:
   - What is the problem?
   - What proofs confirm the solution?

2. **Write failing BDD feature** in `tests/behavior/features/`

3. **Implement code** in `src/devsynth/`

4. **Write tests** that verify implementation

5. **Update documentation** to reflect changes

**Never write code before specification and failing test exist.**

## Pre-Commit Validation

Before any commit:

```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=fast
poetry run python scripts/verify_test_markers.py --changed
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/dialectical_audit.py
```

## Directory Structure

### Source Code (`src/devsynth/`)
- Agent services and application logic
- Follow specification-first workflow
- Adhere to Security and Dialectical Audit policies
- All changes require accompanying tests

### Tests (`tests/`)
- Mirror source structure
- Each test needs **exactly one** speed marker: `fast`, `medium`, or `slow`
- Guard optional services with environment flags
- Use `global_test_isolation` fixture

### Documentation (`docs/`)
- Capture requirements in `docs/specifications/` before implementation
- Follow Documentation Policies
- Resolve `dialectical_audit.log` before submission

### Scripts (`scripts/`)
- Automation and validation tools
- Run via `poetry run python scripts/<script>.py`

## Core Commands

### Testing
```bash
# By speed category (preferred)
poetry run devsynth run-tests --speed=fast
poetry run devsynth run-tests --speed=medium

# Smoke test (fastest sanity)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# With HTML report
poetry run devsynth run-tests --report
```

### Quality Checks
```bash
poetry run black .                    # Format code
poetry run isort .                    # Sort imports
poetry run flake8 src/ tests/         # Lint
poetry run mypy src tests             # Type check
```

### Verification
```bash
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/dialectical_audit.py
```

## Dependencies

### Core Installation
```bash
poetry install --with dev --extras "tests retrieval chromadb api"
```

### Optional Extras
- `minimal`: Baseline runtime
- `retrieval`: Kuzu and FAISS
- `chromadb`: ChromaDB vector store
- `memory`: Full memory backends
- `llm`: Tiktoken and HTTP clients
- `api`: FastAPI and Prometheus
- `webui`: Streamlit interface
- `gui`: Dear PyGui
- `offline`: Transformers

### Resource Flags
```bash
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
# etc.
```

## Conventional Commits

Format: `type(scope): brief summary`

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`, `style`

**Examples**:
```
feat(cli): add --offline mode for providers
fix(memory): handle TinyDB TypeError during insert
docs(readme): clarify installation steps
```

## GitHub Actions Note

All workflows currently disabled. Must trigger manually via `workflow_dispatch` until `v0.1.0a1` tag created.

## Key References

- **Architecture**: `docs/architecture/`
- **Policies**: `docs/policies/`
- **Contributing**: `CONTRIBUTING.md`
- **Specifications**: `docs/specifications/`
- **Testing Standards**: `docs/TESTING_STANDARDS.md`

