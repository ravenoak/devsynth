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
- **Virtual Environment**: Poetry-managed in-project (`.venv/` directory)

### Poetry Virtual Environment Management

**Dialectical Foundation for Virtual Environment Strategy:**

**Thesis**: Centralized virtual environment management ensures consistency and isolation across development environments.

**Antithesis**: System-wide Python installations can lead to dependency conflicts and inconsistent environments across team members and deployment targets.

**Synthesis**: Poetry's in-project virtual environment (`.venv/`) provides project-local dependency isolation while maintaining consistency across development environments and deployment targets.

**This project uses in-project virtual environments enforced via `poetry.toml`:**
```toml
[virtualenvs]
create = true      # Auto-create virtual environment
in-project = true  # Create .venv/ in project directory
```

**Core Principles:**
- Virtual environment is created in `.venv/` within the project directory
- All Python commands must use `poetry run` to execute within the virtual environment
- Never activate the virtual environment manually (`source .venv/bin/activate`)
- Virtual environment path should be `.venv` relative to project root
- All team members should use identical Poetry version and Python version

### Setup Verification & Troubleshooting

**Verification Commands:**
```bash
# 1. Verify Python version (system Python)
python --version              # Must show exactly 3.12.x
which python3.12             # Confirm Python 3.12 location

# 2. Verify Poetry environment configuration
poetry env info --path        # Must print: /path/to/project/.venv
poetry env info               # Show detailed environment info
poetry --version              # Must show Poetry 2.x

# 3. Verify virtual environment Python
poetry run python --version   # Must show 3.12.x from .venv

# 4. Verify task runner
task --version                # Must show go-task version

# 5. Test DevSynth CLI functionality
poetry run devsynth --help    # Confirm CLI works within Poetry env
```

**Troubleshooting Common Issues:**

**Problem**: `python --version` shows wrong version or "command not found"
**Solution**:
```bash
# Check available Python versions
ls /opt/homebrew/bin/python*
# or
ls /usr/bin/python*

# Use full path if needed
/opt/homebrew/bin/python3.12 --version

# Update PATH if necessary
export PATH="/opt/homebrew/bin:$PATH"
```

**Problem**: `poetry env info --path` shows nothing or wrong path
**Solution**:
```bash
# 1. Remove existing environment
poetry env remove 3.12

# 2. Recreate with correct configuration
poetry env use 3.12
poetry install --with dev --extras "tests retrieval chromadb api"

# 3. Verify recreation
poetry env info --path
ls -la .venv/bin/python

# 4. If still broken, check poetry.toml
cat poetry.toml
```

**Problem**: `poetry run devsynth --help` fails
**Solution**:
```bash
# 1. Check if dependencies are installed
poetry install --with dev

# 2. Verify CLI entry point exists
cat pyproject.toml | grep -A 5 "scripts"

# 3. Check if devsynth module exists
poetry run python -c "import devsynth; print('OK')"
```

**Problem**: Import errors or missing dependencies
**Solution**:
```bash
# Reinstall with all extras
poetry install --with dev --extras "tests retrieval chromadb api"

# Check dependency resolution
poetry show

# Update dependencies if needed
poetry update
```

### Working with Poetry Environments

**Dependency Management Philosophy:**

**Thesis**: Comprehensive dependency management ensures reproducible builds and consistent development environments across all team members and deployment targets.

**Antithesis**: Over-reliance on optional dependencies can lead to inconsistent environments and "works on my machine" issues that waste development time.

**Synthesis**: Poetry's extras system provides flexible dependency management while maintaining environment consistency through explicit group definitions and platform-specific markers.

**Installing Dependencies:**
```bash
# Install base runtime dependencies only
poetry install

# Install with development dependencies (recommended for development)
poetry install --with dev

# Install with all extras for full development and testing
poetry install --with dev --extras "tests retrieval chromadb api"

# Install specific extra groups only (for targeted development)
poetry install --with dev --extras "api webui"
```

**Understanding Extras Groups:**

**Core Groups:**
- `dev`: Development tools (black, mypy, pytest, pre-commit, etc.)
- `tests`: Testing extras (additional test dependencies for full test suite)
- `docs`: Documentation building tools (mkdocs, etc.)

**Feature Groups:**
- `retrieval`: Vector retrieval capabilities (kuzu, faiss-cpu)
- `chromadb`: ChromaDB vector store integration
- `memory`: Full memory backend implementations
- `llm`: Tiktoken and HTTP clients for LLM integration
- `api`: FastAPI server and Prometheus monitoring
- `webui`: Streamlit web interface
- `gui`: Dear PyGui desktop interface
- `offline`: Transformers for offline LLM capabilities

**Platform-Specific Dependencies:**
- Some dependencies have platform markers (e.g., `faiss-cpu` only on non-Darwin or ARM64 macOS)
- Use `poetry show` to verify installed packages
- Use `poetry show --tree` to see dependency tree and understand conflicts

**Running Commands:**
```bash
# WRONG - runs in system Python
python script.py

# CORRECT - runs in Poetry virtual environment
poetry run python script.py

# For any Python tool or script
poetry run black .
poetry run pytest tests/
poetry run mypy src/
```

**Environment Troubleshooting:**
```bash
# If poetry env info --path shows nothing or wrong path
poetry env use 3.12
poetry install --with dev --extras tests

# Verify virtual environment is active
poetry run which python  # Should show .venv/bin/python
```

### Environment Variables

**Required for Development:**
```bash
# Test resource flags (set to enable optional test suites)
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true

# Security flags (required for production-like testing)
export DEVSYNTH_AUTHENTICATION_ENABLED=true
export DEVSYNTH_ENCRYPTION_AT_REST=true
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

