---
title: "Poetry Virtual Environment Management Guide"
date: "2025-10-08"
version: "0.1.0-alpha.1"
tags: ["development", "poetry", "virtual-environment", "python"]
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-08"
---

# Poetry Virtual Environment Management Guide

## Overview

This guide provides comprehensive guidance for managing Poetry virtual environments in the DevSynth project, ensuring consistent development environments across all team members and deployment targets.

## Philosophy

**Thesis**: Centralized virtual environment management ensures consistency and isolation across development environments.

**Antithesis**: System-wide Python installations can lead to dependency conflicts and inconsistent environments across team members and deployment targets.

**Synthesis**: Poetry's in-project virtual environment (`.venv/`) provides project-local dependency isolation while maintaining consistency across development environments and deployment targets.

## Configuration

### Poetry Configuration

The project uses in-project virtual environments configured in `poetry.toml`:

```toml
[virtualenvs]
create = true      # Auto-create virtual environment
in-project = true  # Create .venv/ in project directory
```

### Core Principles

- **Project-local**: Virtual environment lives in `.venv/` within project directory
- **Poetry-managed**: All Python commands use `poetry run` to execute within virtual environment
- **No manual activation**: Never use `source .venv/bin/activate`
- **Consistent Python version**: All team members use identical Poetry and Python versions
- **Reproducible**: Same environment across development, CI, and deployment

## Setup and Installation

### Initial Setup

1. **Verify Python Version**
   ```bash
   python --version              # Must show exactly 3.12.x
   which python3.12             # Confirm Python 3.12 location
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   # Using official installer
   curl -sSL https://install.python-poetry.org | python3 -

   # Or using pip (Python 3.12+)
   pip3.12 install poetry
   ```

3. **Verify Poetry Installation**
   ```bash
   poetry --version              # Must show Poetry 2.x
   which poetry                  # Confirm Poetry location
   ```

4. **Configure Poetry for Project**
   ```bash
   # Navigate to project directory
   cd /path/to/devsynth

   # Verify poetry.toml configuration
   cat poetry.toml

   # Create/verify virtual environment
   poetry env use 3.12
   poetry install --with dev --extras "tests retrieval chromadb api"
   ```

### Environment Verification

**Complete Setup Verification:**
```bash
# 1. Verify Python version (system Python)
python --version              # Must show exactly 3.12.x

# 2. Verify Poetry environment configuration
poetry env info --path        # Must print: /path/to/project/.venv
poetry env info               # Show detailed environment info

# 3. Verify virtual environment Python
poetry run python --version   # Must show 3.12.x from .venv

# 4. Verify task runner
task --version                # Must show go-task version

# 5. Test DevSynth CLI functionality
poetry run devsynth --help    # Confirm CLI works within Poetry env

# 6. Verify key dependencies
poetry run python -c "import devsynth; print('DevSynth import OK')"
poetry run python -c "import pytest; print('Pytest OK')"
```

## Working with Dependencies

### Dependency Groups

**Core Groups:**
- `dev`: Development tools (black, mypy, pytest, pre-commit, etc.)
- `tests`: Testing extras (additional test dependencies)
- `docs`: Documentation building tools (mkdocs, etc.)

**Feature Groups:**
- `retrieval`: Vector retrieval (kuzu, faiss-cpu)
- `chromadb`: ChromaDB vector store
- `memory`: Full memory backends
- `llm`: Tiktoken and HTTP clients
- `api`: FastAPI and Prometheus
- `webui`: Streamlit interface
- `gui`: Dear PyGui interface
- `offline`: Transformers for offline LLM

### Installation Commands

```bash
# Install base runtime dependencies only
poetry install

# Install with development dependencies (recommended)
poetry install --with dev

# Install with all extras for full development
poetry install --with dev --extras "tests retrieval chromadb api"

# Install specific groups only
poetry install --with dev --extras "api webui"

# Update all dependencies
poetry update

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree
```

## Running Commands

### Correct Usage

**✅ Do: Use `poetry run` for all Python commands**
```bash
# Correct - runs in Poetry virtual environment
poetry run python script.py
poetry run pytest tests/
poetry run black .
poetry run mypy src/
poetry run devsynth --help
```

**❌ Don't: Run commands directly**
```bash
# Wrong - runs in system Python
python script.py
pytest tests/
black .
```

### Environment Variables

**Required for Development:**
```bash
# Test resource flags
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true

# Security flags (for production-like testing)
export DEVSYNTH_AUTHENTICATION_ENABLED=true
export DEVSYNTH_ENCRYPTION_AT_REST=true

# Property testing (opt-in)
export DEVSYNTH_PROPERTY_TESTING=true
```

## Troubleshooting

### Common Issues and Solutions

#### Problem: Wrong Python Version

**Symptoms:** `python --version` shows wrong version or "command not found"

**Solutions:**
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

#### Problem: Poetry Environment Issues

**Symptoms:** `poetry env info --path` shows nothing or wrong path

**Solutions:**
```bash
# 1. Remove existing environment
poetry env remove 3.12

# 2. Recreate with correct configuration
poetry env use 3.12
poetry install --with dev --extras "tests retrieval chromadb api"

# 3. Verify recreation
poetry env info --path
ls -la .venv/bin/python

# 4. Check poetry.toml configuration
cat poetry.toml
```

#### Problem: Import Errors or Missing Dependencies

**Symptoms:** `poetry run devsynth --help` fails or import errors

**Solutions:**
```bash
# 1. Reinstall dependencies
poetry install --with dev --extras "tests retrieval chromadb api"

# 2. Check dependency resolution
poetry show
poetry show --tree

# 3. Verify CLI entry point
cat pyproject.toml | grep -A 5 "scripts"

# 4. Test module import
poetry run python -c "import devsynth; print('OK')"
```

#### Problem: Test Environment Issues

**Symptoms:** Tests fail due to missing optional dependencies

**Solutions:**
```bash
# 1. Install test extras
poetry install --with dev --extras "tests"

# 2. Set resource flags
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true

# 3. Verify test environment
poetry run which pytest
poetry run pytest --collect-only -q | head -10
```

## Advanced Usage

### Multiple Python Versions

**For testing across Python versions:**
```bash
# Create environment for different Python version
poetry env use 3.11
poetry install

# Switch back to primary version
poetry env use 3.12
poetry install
```

### Dependency Locking

**For reproducible builds:**
```bash
# Generate lock file
poetry lock

# Install from lock file only
poetry install --locked

# Update specific dependencies
poetry update package_name
```

### Development Workflow

**Typical development session:**
```bash
# 1. Activate project directory
cd /path/to/devsynth

# 2. Verify environment
poetry env info --path

# 3. Install/update dependencies
poetry install --with dev

# 4. Run development commands
poetry run devsynth run-tests --speed=fast
poetry run black .
poetry run mypy src/

# 5. Test changes
poetry run python -m pytest tests/unit/test_my_feature.py -v
```

## CI/CD Integration

### GitHub Actions

**Example workflow configuration:**
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.12'

- name: Install Poetry
  run: |
    curl -sSL https://install.python-poetry.org | python3 -
    echo "$HOME/.local/bin" >> $GITHUB_PATH

- name: Configure Poetry
  run: |
    poetry config virtualenvs.in-project true

- name: Install dependencies
  run: |
    poetry install --with dev --extras "tests retrieval chromadb api"
```

### Docker Integration

**For containerized environments:**
```dockerfile
# Use Poetry to manage dependencies
FROM python:3.12-slim

# Install Poetry
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.in-project true

# Copy project files
WORKDIR /app
COPY pyproject.toml poetry.toml ./

# Install dependencies
RUN poetry install --only=main --no-dev
```

## Best Practices

### Team Consistency

1. **Use identical Poetry versions** across all team members
2. **Use identical Python versions** (exactly 3.12.x)
3. **Commit `.venv/` to version control** for faster CI/CD
4. **Use `poetry run` consistently** for all Python commands
5. **Document environment requirements** in setup guides

### Environment Hygiene

1. **Don't commit secrets** to environment files
2. **Use `.env` for local development** (never commit)
3. **Set resource flags explicitly** for optional features
4. **Clean environments regularly** to avoid dependency bloat
5. **Test environment portability** across different systems

### Troubleshooting Workflow

1. **Verify environment setup** with verification commands
2. **Check Poetry configuration** in `poetry.toml`
3. **Reinstall dependencies** if issues persist
4. **Check system Python** and Poetry versions
5. **Consult team** for environment-specific issues

## Support

For Poetry or virtual environment issues:

1. Check this guide for common solutions
2. Review project setup scripts (`scripts/install_dev.sh`)
3. Consult team members with similar environments
4. Check Poetry documentation for advanced issues
5. Open issue with `area/environment` label for persistent problems

## References

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python Virtual Environments Guide](https://docs.python.org/3/library/venv.html)
- [Project Setup Scripts](../getting_started/setup-scripts.md)
- [Development Environment Guide](../getting_started/development-environment.md)
