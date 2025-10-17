---
description: Poetry dependency management and virtual environment workflow
globs:
  - "pyproject.toml"
  - "poetry.lock"
  - "poetry.toml"
  - ".venv/**"
alwaysApply: false
---

# DevSynth Poetry & Virtual Environment Management

## Philosophy

**Dependency management is infrastructure, not an afterthought.** Poetry provides deterministic, reproducible environments that ensure:

- **Isolation**: No conflicts between projects
- **Reproducibility**: `poetry.lock` ensures identical environments
- **Consistency**: All team members use identical dependency versions
- **Automation**: Scripts and tools work reliably across environments

## Virtual Environment Architecture

### In-Project Virtual Environments

**This project mandates in-project virtual environments:**

```toml
# poetry.toml (committed)
[virtualenvs]
create = true
in-project = true
```

**Benefits:**
- `.venv/` is committed to version control (only the directory, not contents)
- Clear separation between system and project Python environments
- Easy identification of active project environment
- Simplified CI/CD environment setup

**Directory Structure:**
```
project/
├── .venv/              # Virtual environment (gitignored)
├── pyproject.toml      # Project configuration
├── poetry.lock         # Locked dependency versions
└── poetry.toml         # Poetry configuration (committed)
```

## Dependency Categories

### Core Dependencies (`[tool.poetry.dependencies]`)

**Runtime requirements - always installed:**
- `python = "<3.13,>=3.12"` - Python version constraint
- `typer`, `rich`, `pydantic` - Core CLI and data handling
- `langgraph`, `langchain` - Agent orchestration
- `cryptography`, `argon2-cffi` - Security primitives

### Optional Dependencies (`[project.optional-dependencies]`)

**Feature flags for different use cases:**

```bash
# Minimal runtime (CI smoke tests)
poetry install --extras minimal

# Full development environment
poetry install --with dev --extras "tests retrieval chromadb api"

# Memory backends for testing
poetry install --with dev --extras memory

# GUI development
poetry install --with dev --extras gui
```

### Development Dependencies (`[tool.poetry.group.dev.dependencies]`)

**Quality assurance and development tools:**
- `pytest`, `pytest-bdd` - Testing frameworks
- `black`, `isort`, `flake8` - Code formatting and linting
- `mypy` - Type checking
- `pre-commit` - Git hooks
- `bandit`, `safety` - Security scanning

## Workflow Commands

### Environment Setup

```bash
# Initial setup (one-time)
poetry env use 3.12                    # Ensure Python 3.12
poetry install --with dev --extras tests  # Full development setup

# Verify environment
poetry env info --path                 # Should show .venv/ path
poetry run python --version            # Should show Python 3.12.x
poetry run devsynth --help             # Should work without errors
```

### Daily Development

```bash
# Add new dependency
poetry add package-name
poetry add --group dev development-package

# Add optional dependency
poetry add --optional package-name
# Then manually add to [project.optional-dependencies] section

# Update dependencies
poetry update                          # Update all
poetry update package-name             # Update specific package

# Remove dependency
poetry remove package-name
```

### Running Commands

**Always use `poetry run` for any Python command:**

```bash
# Correct usage
poetry run python scripts/verify_test_markers.py
poetry run pytest tests/unit/
poetry run black src/
poetry run mypy src/

# Incorrect usage (uses system Python)
python scripts/verify_test_markers.py
pytest tests/unit/
```

### Environment Management

```bash
# Check environment status
poetry env info

# List all environments for this project
poetry env list

# Remove and recreate environment (nuclear option)
poetry env remove --all
poetry install --with dev --extras tests
```

## Dependency Resolution Principles

### Version Constraints

**Follow semantic versioning with care:**

```toml
# Good - allows patch updates within minor version
package = "^1.2.3"

# Careful - allows breaking changes
package = "*"

# Specific - for unstable or problematic packages
fastapi = {version = "^0.115.0", extras = ["all"]}
starlette = {version = "^0.37.0"}
```

### Platform-Specific Dependencies

**Handle platform variations appropriately:**

```toml
# Architecture-specific (Linux/x86_64 only)
kuzu = {version = "*", optional = true, markers = "platform_system == \"Linux\" and platform_machine == \"x86_64\""}

# macOS compatibility (exclude ARM64 for some packages)
faiss-cpu = {version = "*", optional = true, markers = "platform_system != \"Darwin\" or platform_machine == \"arm64\""}
```

## Quality Assurance

### Lock File Management

**`poetry.lock` must always be committed:**

```bash
# After dependency changes
poetry lock --no-update                  # Refresh lock without updating
git add poetry.lock

# Check for outdated dependencies
poetry show --outdated
```

### Dependency Auditing

```bash
# Security vulnerability scanning
poetry run safety check

# Check for incompatible versions
poetry check

# Verify all dependencies can be resolved
poetry lock --check
```

## Troubleshooting

### Common Issues

**1. "No module named" errors:**
```bash
# Wrong - uses system Python
pip install package

# Right - installs in Poetry environment
poetry add package
```

**2. Environment not found:**
```bash
poetry env remove --all
poetry env use 3.12
poetry install --with dev --extras tests
```

**3. Lock file conflicts:**
```bash
# Discard local changes and use lock file
poetry install --sync

# Update specific package
poetry update package-name
```

**4. Platform-specific installation failures:**
```bash
# Check platform markers
poetry show --tree | grep -A 5 -B 5 "platform"

# Install without problematic extras
poetry install --with dev --extras "tests chromadb"
```

### Environment Variables

**Required for full functionality:**

```bash
# Enable optional test resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true

# Security configuration
export DEVSYNTH_ENCRYPTION_AT_REST=true
export DEVSYNTH_AUTHENTICATION_ENABLED=true
```

## Integration with CI/CD

### CI Environment Setup

```yaml
# .github/workflows/ci.yml pattern
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: "3.12"

- name: Install Poetry
  run: |
    pip install poetry
    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true

- name: Install dependencies
  run: poetry install --with dev --extras "tests retrieval chromadb api"
```

### Local vs CI Consistency

**Ensure local and CI environments match:**
- Same Python version (3.12)
- Same Poetry configuration
- Same environment variables
- Same optional extras enabled

## Best Practices

### Dependency Hygiene

- **Minimize dependencies**: Each dependency increases maintenance burden
- **Prefer stable versions**: Avoid development releases in production
- **Regular updates**: Keep dependencies current for security
- **Test after updates**: Always run full test suite after dependency changes

### Virtual Environment Discipline

- **Never activate manually**: Always use `poetry run`
- **Keep environments clean**: Remove unused environments periodically
- **Document requirements**: Update `pyproject.toml` comments for complex dependencies
- **Version control Poetry config**: `poetry.toml` should be committed

### Collaboration

- **Communicate dependency changes**: Notify team of new or updated dependencies
- **Test across platforms**: Ensure platform-specific dependencies work
- **Document environment setup**: Keep setup instructions current
- **Use consistent extras**: Agree on which extras to use for different scenarios

## References

- **Poetry Documentation**: https://python-poetry.org/docs/
- **PEP 621**: https://peps.python.org/pep-0621/ (pyproject.toml standard)
- **Semantic Versioning**: https://semver.org/
- **Project Dependencies**: `pyproject.toml` (in repository root)
