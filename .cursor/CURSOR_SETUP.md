# DevSynth Cursor IDE Setup Guide

This guide provides Cursor IDE-specific setup instructions for DevSynth development, replacing any Codex-specific workflows.

## Prerequisites

- **Cursor IDE** installed and configured
- **Python 3.12** available on your system
- **Poetry** for dependency management
- **Git** for version control

## Initial Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd devsynth
```

### 2. Python Environment Setup
```bash
# Verify Python 3.12 is available
python --version  # should show 3.12.x

# Create Poetry environment with Python 3.12
poetry env use 3.12

# Verify environment creation
poetry env info --path  # must print the virtualenv path
```

### 3. Development Environment Provisioning
```bash
# Run the standard development setup (NOT codex_setup.sh)
bash scripts/install_dev.sh

# Verify task runner is available
task --version
```

### 4. Install Dependencies
```bash
# Install with development and testing extras
poetry install --with dev --extras "tests retrieval chromadb api"
```

### 5. Verify Installation
```bash
# Test CLI availability
poetry run devsynth --help

# Test collection works
poetry run pytest --collect-only -q

# Verify key tools
poetry run pre-commit --version
poetry run python scripts/verify_test_markers.py --help
```

## Cursor IDE Configuration

### Rules Files
The `.cursor/rules` file provides comprehensive guidance for LLM agents working in this project. Key features:

- **BDD Workflow Enforcement**: Ensures specification-first development
- **Test Discipline**: Maintains speed markers and resource flags
- **Command Patterns**: Correct Poetry and CLI usage
- **Quality Standards**: Formatting, linting, security compliance

### Workspace Settings
Cursor IDE will automatically use the rules configuration. Ensure:

1. **Project Rules**: `.cursor/rules` is recognized by Cursor
2. **File Organization**: Understand where different code types belong
3. **Testing Patterns**: Use the provided test execution commands
4. **Quality Checks**: Pre-commit hooks are installed and working

## Key Differences from Codex

| Aspect | Codex (AGENTS.md) | Cursor IDE (.cursor/rules) |
|--------|-------------------|---------------------------|
| **Setup Script** | `scripts/codex_setup.sh` | `scripts/install_dev.sh` only |
| **Environment** | Codex-specific provisioning | Standard Poetry + development tools |
| **Rules Location** | `AGENTS.md` files | `.cursor/rules` directory |
| **Agent Guidance** | Codex agent patterns | Cursor IDE LLM agent patterns |
| **Workflow Focus** | Codex environment constraints | Cursor IDE development workflow |

## Important Warnings

### ❌ Do NOT Use These (Codex-Specific)
- `AGENTS.md` files (these are for Codex environments)
- `scripts/codex_setup.sh` (will cause conflicts)
- Any Codex-specific environment variables or configurations

### ✅ Use These Instead (Cursor IDE-Specific)
- `CONTRIBUTING.md` (primary setup reference)
- `.cursor/rules` (comprehensive agent guidance)
- `scripts/install_dev.sh` (standard development setup)
- Poetry and task runner for all operations

## Development Workflow

### 1. Specification-First Development
```bash
# Always start with specification
touch docs/specifications/new_feature.md

# Create failing BDD test
touch tests/behavior/features/new_feature.feature

# Confirm test fails
poetry run pytest tests/behavior/features/new_feature.feature

# Then implement
```

### 2. Test Execution
```bash
# Fast smoke test
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# Full test suite by speed
poetry run devsynth run-tests --target unit-tests --speed=fast
poetry run devsynth run-tests --target integration-tests --speed=fast
poetry run devsynth run-tests --target behavior-tests --speed=fast
```

### 3. Quality Assurance
```bash
# Pre-commit checks
poetry run pre-commit run --all-files

# Test marker verification
poetry run python scripts/verify_test_markers.py

# Security and audit compliance
poetry run python scripts/dialectical_audit.py
```

## Troubleshooting

### Common Issues

**Q: Poetry environment not found**
```bash
poetry env use 3.12
poetry install --with dev --extras "tests retrieval chromadb api"
```

**Q: Task command not available**
```bash
bash scripts/install_dev.sh
export PATH="$HOME/.local/bin:$PATH"
```

**Q: Tests failing with import errors**
```bash
poetry install --with dev --extras "tests retrieval chromadb api"
poetry run pytest --collect-only -q
```

**Q: Pre-commit hooks not working**
```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg
```

### Validation

Run the validation script to ensure everything is configured correctly:
```bash
poetry run python .cursor/validate-rules.py
```

This should show all green checkmarks for a properly configured Cursor IDE environment.

## Next Steps

1. **Read the Rules**: Review `.cursor/rules` for comprehensive development guidance
2. **Practice BDD**: Try the specification-first workflow on a small feature
3. **Test Integration**: Run the integration tests in `.cursor/integration-test.md`
4. **Quality Checks**: Ensure all pre-commit hooks and validation scripts pass

## Support

If you encounter issues specific to Cursor IDE integration:

1. Check `.cursor/validate-rules.py` output
2. Review `.cursor/integration-test.md` scenarios
3. Ensure you're not mixing Codex-specific instructions
4. Verify all dependencies are installed via Poetry

Remember: This project is optimized for Cursor IDE workflows. Using Codex-specific instructions will cause conflicts and should be avoided.
