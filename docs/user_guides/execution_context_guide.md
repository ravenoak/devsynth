# DevSynth Execution Context Guide

**Author**: DevSynth Team
**Date**: 2024-09-24
**Version**: v0.1.0a1
**Status**: Critical for Alpha Release

## Overview

This guide explains how to properly execute DevSynth commands in different contexts, particularly important for the v0.1.0a1 alpha release where the execution model has specific requirements.

## Execution Methods for v0.1.0a1

### Method 1: Poetry-Based Execution (RECOMMENDED)

**Use Case**: Development, testing, and alpha evaluation
**Requirement**: Must be executed from within the DevSynth project directory

```bash
# Navigate to DevSynth project directory
cd /path/to/devsynth/project

# All DevSynth commands must be run with poetry run
poetry run devsynth init
poetry run devsynth spec --requirements-file requirements.md
poetry run devsynth test --spec-file specs.md
poetry run devsynth code
poetry run devsynth run-pipeline
```

**Advantages:**
- ✅ Guaranteed to work with all dependencies
- ✅ Uses correct Python version and virtual environment
- ✅ All features and extras available
- ✅ Consistent with development workflow

**Limitations:**
- ❌ Must be in DevSynth project directory
- ❌ Requires Poetry to be installed
- ❌ Not suitable for global system installation

### Method 2: Direct Virtual Environment Execution

**Use Case**: When you need to run DevSynth from any directory
**Requirement**: Know the path to DevSynth's virtual environment

```bash
# Get the virtual environment path (run from DevSynth project)
cd /path/to/devsynth/project
DEVSYNTH_VENV="$(poetry env info --path)"

# Now you can run DevSynth from any directory
cd /any/directory
$DEVSYNTH_VENV/bin/devsynth --help
$DEVSYNTH_VENV/bin/devsynth init
```

**Advantages:**
- ✅ Can run from any directory
- ✅ Uses correct dependencies and Python version
- ✅ All features available

**Limitations:**
- ❌ Requires knowing the venv path
- ❌ Path may change if venv is recreated
- ❌ More complex setup

### Method 3: pipx Installation (POST-ALPHA)

**Use Case**: Global system installation for end users
**Status**: Not fully functional for v0.1.0a1 due to dependency issues

```bash
# Current issues (to be resolved post-alpha):
# 1. Python version constraints (requires <3.13, >=3.12)
# 2. Dependency resolution for click/typer
# 3. Optional extras not automatically installed

# Future working approach (post-alpha):
pipx install devsynth
devsynth --help  # Works from any directory
```

**Future Advantages:**
- ✅ Global installation
- ✅ Isolated environment
- ✅ Works from any directory
- ✅ Standard Python package installation

**Current Limitations:**
- ❌ Dependency resolution issues
- ❌ Python version constraint problems
- ❌ Not ready for v0.1.0a1 alpha release

## Real-World Testing Implications

### For Manual Testing

When executing the real-world test scenarios:

```bash
# Correct approach for v0.1.0a1
DEVSYNTH_PROJECT="/path/to/devsynth"
TEST_DIR="/tmp/my_test_project"

# Step 1: Create test directory
mkdir -p "$TEST_DIR"

# Step 2: Initialize project (from DevSynth directory)
cd "$DEVSYNTH_PROJECT"
# Note: init command works in current directory, so we need to:
cd "$TEST_DIR"
"$DEVSYNTH_PROJECT"/.venv/bin/devsynth init

# Step 3: Continue workflow
# Create requirements.md in test directory
cat > requirements.md << 'EOF'
# My Project Requirements
...
EOF

# Step 4: Generate specs (from DevSynth directory, targeting test directory)
cd "$DEVSYNTH_PROJECT"
poetry run devsynth spec --requirements-file "$TEST_DIR/requirements.md"
# Output will be generated in current directory, may need to move files
```

### For Automated Testing

The automated test framework handles this correctly by:
- Using temporary directories for test isolation
- Mocking the DevSynth CLI behavior for testing
- Running within the proper Poetry context
- Cleaning up artifacts appropriately

## Recommended Workflow for Alpha Users

### For Developers Evaluating DevSynth

1. **Clone and Setup DevSynth**:
   ```bash
   git clone https://github.com/ravenoak/devsynth.git
   cd devsynth
   poetry install --with dev --extras "tests retrieval chromadb api"
   ```

2. **Create Test Projects**:
   ```bash
   # Create your test project directory
   mkdir ~/my_devsynth_test
   cd ~/my_devsynth_test

   # Initialize from DevSynth directory
   cd /path/to/devsynth
   poetry run devsynth init
   # Follow the interactive wizard
   ```

3. **Development Workflow**:
   ```bash
   # Always run DevSynth commands from the DevSynth project directory
   cd /path/to/devsynth

   # But work on your project files in your project directory
   # Edit requirements.md in your project directory
   # Then generate specs:
   poetry run devsynth spec --requirements-file /path/to/your/project/requirements.md
   ```

### For Advanced Users

If you need to run DevSynth from any directory, use the direct venv approach:

```bash
# One-time setup
cd /path/to/devsynth
DEVSYNTH_VENV="$(poetry env info --path)"
echo "export DEVSYNTH_VENV='$DEVSYNTH_VENV'" >> ~/.bashrc
source ~/.bashrc

# Then from any directory:
$DEVSYNTH_VENV/bin/devsynth --help
```

## Post-Alpha Improvements

### Planned for v0.1.1+

1. **pipx Compatibility**: Resolve dependency issues for global installation
2. **Path Independence**: Improve CLI to work from any directory
3. **Configuration Management**: Better handling of project context detection
4. **Installation Simplification**: Streamlined setup for end users

### Migration Path

Once pipx installation is fixed:
```bash
# Future (post-alpha) global installation
pipx install devsynth
pipx ensurepath  # Ensure PATH is configured
devsynth --help  # Works from anywhere
```

## Troubleshooting

### Common Issues

1. **"Poetry could not find a pyproject.toml file"**
   - **Cause**: Running `poetry run` outside DevSynth project directory
   - **Solution**: Always run from DevSynth project directory

2. **"ModuleNotFoundError: No module named 'click'"**
   - **Cause**: pipx installation with missing dependencies
   - **Solution**: Use Poetry-based execution for v0.1.0a1

3. **"devsynth: command not found"**
   - **Cause**: DevSynth not in PATH or not installed
   - **Solution**: Use full venv path or Poetry execution

### Validation Commands

Test your setup with these commands:

```bash
# From DevSynth project directory
cd /path/to/devsynth
poetry run devsynth --version
poetry run devsynth doctor
poetry run devsynth --help

# Test venv path approach
VENV_PATH="$(poetry env info --path)"
cd /tmp
$VENV_PATH/bin/devsynth --version
```

---

**Summary**: For v0.1.0a1 alpha release, use Poetry-based execution from the DevSynth project directory. This ensures all dependencies are available and the execution context is correct. pipx installation will be improved in post-alpha releases.
