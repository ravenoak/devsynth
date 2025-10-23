# DevSynth Cursor IDE Setup Guide

This comprehensive guide provides Cursor IDE-specific setup instructions for DevSynth development. It includes platform-specific guidance, practical workflows, and troubleshooting for the complete development environment.

## Prerequisites

- **Cursor IDE** installed and configured (latest version recommended)
- **Python 3.12** available on your system (exact version required)
- **Poetry** for dependency management (version 2.x)
- **Git** for version control
- **go-task** for task automation (installed via setup scripts)

## Platform-Specific Setup

### macOS (Recommended for Development)

**1. Install Python 3.12**
```bash
# Using Homebrew (recommended)
brew install python@3.12

# Verify installation
/opt/homebrew/bin/python3.12 --version
```

**2. Install Poetry**
```bash
# Using pipx (recommended for isolated installation)
pip install pipx
pipx install poetry

# Or using Homebrew
brew install poetry

# Verify installation
poetry --version
```

**3. Configure Poetry for DevSynth**
```bash
# Configure for in-project virtual environments
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Verify configuration
poetry config --list
```

**4. Setup DevSynth Environment**
```bash
# Clone repository
git clone <repository-url>
cd devsynth

# Use exact Python version
poetry env use /opt/homebrew/bin/python3.12

# Install development environment
bash scripts/install_dev.sh

# Install all dependencies
poetry install --with dev --extras "tests retrieval chromadb api"
```

**5. Verify Setup**
```bash
# Check virtual environment
poetry env info --path  # Should show: /path/to/project/.venv

# Test CLI
poetry run devsynth --help

# Verify Cursor integration
poetry run python scripts/verify_cursor_integration.py
```

### Linux (Ubuntu/Debian)

**1. Install Python 3.12**
```bash
# Update system packages
sudo apt update

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify installation
python3.12 --version
```

**2. Install Poetry**
```bash
# Install pipx first
sudo apt install pipx
pipx install poetry

# Or install directly
curl -sSL https://install.python-poetry.org | python3 -
```

**3. Configure Poetry**
```bash
# Enable in-project virtual environments
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
```

**4. Setup Project**
```bash
# Clone and setup
git clone <repository-url>
cd devsynth

# Create environment with system Python
poetry env use python3.12

# Run setup scripts
bash scripts/install_dev.sh

# Install dependencies (note: some extras may not be available on Linux)
poetry install --with dev --extras "tests chromadb api"
```

**5. Verify Setup**
```bash
# Check environment
poetry env info --path  # Should show .venv path

# Test functionality
poetry run devsynth --help

# Run integration check
poetry run python scripts/verify_cursor_integration.py
```

### Windows

**1. Install Python 3.12**
```bash
# Download from python.org and install
# Make sure to check "Add Python to PATH"
# Verify installation
python --version
```

**2. Install Poetry**
```bash
# Using pip (recommended)
pip install poetry

# Or using Chocolatey
choco install poetry
```

**3. Configure Poetry**
```bash
# Enable virtual environments
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
```

**4. Setup Project**
```bash
# Clone repository
git clone <repository-url>
cd devsynth

# Create environment
poetry env use python

# Install dependencies (limited extras on Windows)
poetry install --with dev --extras "tests api"

# Run setup scripts (some may not work on Windows)
bash scripts/install_dev.sh
```

**5. Environment Variables**
```bash
# Set required environment variables
set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
set DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
```

**6. Verify Setup**
```bash
# Check environment
poetry env info --path

# Test CLI
poetry run devsynth --help
```

## Common Environment Variables

Set these for full functionality:

```bash
# Required for optional test resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true

# Security and authentication (development)
export DEVSYNTH_AUTHENTICATION_ENABLED=true
export DEVSYNTH_ENCRYPTION_AT_REST=true

# Optional: Enable property-based testing
export DEVSYNTH_PROPERTY_TESTING=true
```

## Cursor IDE Integration

### Opening Project in Cursor

**1. Launch Cursor IDE**
```bash
# Open project in Cursor
cursor .
```

**2. Verify Integration**
```bash
# Check that rules are loaded (Cursor should show rule indicators)
# Verify environment is active in terminal
poetry run python --version  # Should show 3.12.x from .venv
```

**3. Test Cursor Commands**
```bash
# Try a simple Cursor command in chat
/expand-phase add user authentication

# Should receive structured response following EDRR framework
```

### Cursor IDE Features for DevSynth

#### Chat Interface Integration
- **EDRR Commands**: Use `/expand-phase`, `/differentiate-phase`, `/refine-phase`, `/retrospect-phase`
- **Specification Commands**: `/generate-specification`, `/validate-bdd-scenarios`
- **Testing Commands**: `/generate-test-suite`, `/code-review`
- **Context Awareness**: Cursor automatically loads project context and specifications

#### Composer Mode Integration
- **Rule Guidance**: Cursor composer applies project rules automatically
- **Specification Integration**: Easy access to `docs/specifications/` during code generation
- **Test Integration**: Generate code with corresponding tests automatically
- **Quality Gates**: Built-in compliance with project standards

#### Code Generation with Context
```bash
# Example: Generate a new feature with full context
/generate-specification user profile management

# Cursor will:
# 1. Create specification in docs/specifications/
# 2. Generate BDD scenarios in tests/behavior/features/
# 3. Provide implementation guidance with examples
```

### Custom Modes Setup

Cursor provides custom modes optimized for DevSynth workflows:

#### EDRRImplementer Mode (`Cmd+Shift+E`)
- **Purpose**: Implementation within EDRR framework
- **Features**: Structured implementation guidance, automatic test generation
- **Use Case**: When implementing new features or components

#### SpecArchitect Mode (`Cmd+Shift+S`)
- **Purpose**: Specification and BDD scenario creation
- **Features**: SDD workflow guidance, Gherkin generation
- **Use Case**: When defining new features or requirements

#### TestArchitect Mode (`Cmd+Shift+T`)
- **Purpose**: Comprehensive test suite creation
- **Features**: Unit, integration, and BDD test generation
- **Use Case**: When building or enhancing test coverage

#### CodeReviewer Mode (`Cmd+Shift+R`)
- **Purpose**: Comprehensive code review and quality assessment
- **Features**: Architecture compliance, security analysis, performance review
- **Use Case**: When reviewing code changes or implementations

#### DialecticalThinker Mode (`Cmd+Shift+D`)
- **Purpose**: Apply dialectical reasoning for decision-making
- **Features**: Multi-perspective analysis, thesis-antithesis-synthesis
- **Use Case**: When making architectural or design decisions

### Cursor IDE Best Practices for DevSynth

#### 1. Always Start with Context
```bash
# Before implementing, review relevant specifications
# Cursor provides easy access to docs/specifications/
# Use /generate-specification for new features
```

#### 2. Follow EDRR Process
```bash
# Use structured approach for all development tasks:
/expand-phase [task description]
/differentiate-phase [options analysis]
/refine-phase [implementation]
/retrospect-phase [learning capture]
```

#### 3. Leverage Testing Integration
```bash
# Generate comprehensive tests automatically
/generate-test-suite [component name]

# Verify implementation with multiple test types
poetry run devsynth run-tests --speed=fast
```

#### 4. Quality Assurance Workflow
```bash
# Use code review for quality assessment
/code-review [recent changes]

# Validate specifications and BDD scenarios
/validate-bdd-scenarios [feature file]
```

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

## Daily Development Workflow

### Complete Feature Development Example

**1. Start with Specification (Using Cursor)**
```bash
# In Cursor chat, use:
/generate-specification user profile management feature

# This creates:
# - docs/specifications/user_profile_management.md
# - tests/behavior/features/user_profile_management.feature
```

**2. Implement with EDRR Process (Using Cursor)**
```bash
# Expand phase - generate multiple approaches
/expand-phase implement user profile management

# Differentiate phase - compare approaches
/differentiate-phase user profile implementation approaches

# Refine phase - implement selected approach
/refine-phase implement FastAPI-based user profile management

# Retrospect phase - capture learnings
/retrospect-phase user profile implementation analysis
```

**3. Testing Workflow (Terminal Integration)**
```bash
# Run fast tests during development
poetry run devsynth run-tests --speed=fast

# Run specific test categories
poetry run pytest tests/unit/ -v --tb=short
poetry run pytest tests/behavior/features/user_profile_management.feature

# Check test coverage
poetry run devsynth run-tests --report
```

**4. Quality Assurance (Using Cursor)**
```bash
# Code review
/code-review user profile management implementation

# Validate BDD scenarios
/validate-bdd-scenarios user_profile_management.feature

# Generate additional tests if needed
/generate-test-suite user profile component
```

### Common Development Tasks

#### Adding a New CLI Command
```bash
# 1. Specification
/generate-specification add offline mode to CLI

# 2. Implementation
/expand-phase implement CLI offline mode
/refine-phase implement offline mode with transformers fallback

# 3. Testing
/generate-test-suite CLI offline functionality

# 4. Integration
poetry run devsynth --help  # Verify new command appears
```

#### Implementing a New Agent
```bash
# 1. Specification
/generate-specification conversation agent with memory

# 2. Architecture
/expand-phase implement agent with memory integration

# 3. Implementation
/refine-phase implement conversation agent using langgraph

# 4. Testing
/generate-test-suite conversation agent
```

#### Adding Database Integration
```bash
# 1. Specification
/generate-specification database integration for user preferences

# 2. Schema Design
/expand-phase database schema options for preferences

# 3. Implementation
/refine-phase implement TinyDB integration for preferences

# 4. Testing
/generate-test-suite database integration tests
```

## Quality Assurance Workflow

### Pre-commit Validation
```bash
# Install pre-commit hooks (one-time setup)
poetry run pre-commit install

# Run all quality checks
poetry run pre-commit run --all-files

# Run specific checks
poetry run pre-commit run black --all-files
poetry run pre-commit run mypy --all-files
```

### Testing Strategy
```bash
# 1. Fast feedback during development
poetry run devsynth run-tests --speed=fast

# 2. Integration testing
poetry run devsynth run-tests --speed=medium

# 3. Full test suite (before commits)
poetry run devsynth run-tests --speed=slow

# 4. Coverage analysis
poetry run devsynth run-tests --report
```

### Code Quality Checks
```bash
# Type checking
poetry run mypy src/

# Code formatting
poetry run black .
poetry run isort .

# Linting
poetry run flake8 src/ tests/

# Security scanning
poetry run bandit -r src/
poetry run safety check
```

### Validation Scripts
```bash
# Verify test markers
poetry run python scripts/verify_test_markers.py

# Requirements traceability
poetry run python scripts/verify_requirements_traceability.py

# Version synchronization
poetry run python scripts/verify_version_sync.py

# Dialectical audit
poetry run python scripts/dialectical_audit.py
```

## Troubleshooting

### Cursor IDE Integration Issues

#### Problem: Cursor Rules Not Applying
**Symptoms**: Commands like `/expand-phase` not working, no rule guidance in chat
**Solutions**:
```bash
# 1. Verify Cursor integration
poetry run python scripts/verify_cursor_integration.py

# 2. Check rule files have proper YAML frontmatter
find .cursor/rules -name "*.mdc" -exec head -5 {} \;

# 3. Restart Cursor IDE and reload project
# 4. Check Cursor settings for custom rules directory
```

#### Problem: Cursor Commands Not Available
**Symptoms**: Chat doesn't recognize `/expand-phase`, `/generate-specification`, etc.
**Solutions**:
```bash
# 1. Verify commands directory exists
ls -la .cursor/commands/

# 2. Check command files are markdown (.md)
find .cursor/commands -name "*.md" | head -5

# 3. Restart Cursor IDE
# 4. Check Cursor version compatibility
```

#### Problem: Context Not Loading
**Symptoms**: AI doesn't reference project specifications or existing code
**Solutions**:
```bash
# 1. Verify project is fully loaded in Cursor workspace
# 2. Check context management settings in modes.json
# 3. Ensure large files aren't excluded by .gitignore
# 4. Try reopening project in Cursor
```

### Poetry Environment Issues

#### Problem: "No module named" Errors
**Symptoms**: Import errors when running Python code
**Solutions**:
```bash
# 1. Verify you're in Poetry environment
poetry run python --version  # Should show .venv Python

# 2. Reinstall dependencies
poetry install --with dev --extras "tests retrieval chromadb api"

# 3. Clear Poetry cache
poetry cache clear --all pypi

# 4. Recreate environment (nuclear option)
poetry env remove --all
poetry env use python3.12  # or python on Windows
poetry install --with dev --extras "tests retrieval chromadb api"
```

#### Problem: Platform-Specific Dependencies Failing
**Symptoms**: Installation errors for kuzu, faiss-cpu, chromadb on certain platforms
**Solutions**:
```bash
# 1. Check platform compatibility
python -c "import platform; print(platform.machine(), platform.system())"

# 2. Install without problematic extras (Linux/macOS)
poetry install --with dev --extras "tests api"

# 3. Install extras individually to isolate issues
poetry install --with dev --extras "tests"
poetry add --optional kuzu  # Test individually

# 4. Use conda for complex scientific packages (if needed)
conda install faiss-cpu chromadb
```

#### Problem: Virtual Environment Path Issues
**Symptoms**: `poetry env info --path` shows wrong path or nothing
**Solutions**:
```bash
# 1. Check Poetry configuration
poetry config --list

# 2. Reset Poetry configuration
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# 3. Remove and recreate environment
poetry env remove --all
poetry env use python3.12  # Use full path if needed
poetry install --with dev

# 4. Verify .venv directory exists
ls -la .venv/bin/python
```

### Testing Issues

#### Problem: Tests Not Running in Cursor Terminal
**Symptoms**: Tests fail when run in Cursor but work in external terminal
**Solutions**:
```bash
# 1. Ensure Cursor terminal uses Poetry environment
poetry run which python  # Should show .venv path

# 2. Set environment variables in Cursor terminal
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true

# 3. Run tests with explicit environment
poetry run devsynth run-tests --speed=fast --no-parallel
```

#### Problem: Missing Test Markers
**Symptoms**: Verification scripts fail with missing speed markers
**Solutions**:
```bash
# 1. Run marker verification
poetry run python scripts/verify_test_markers.py

# 2. Auto-fix missing markers
poetry run python scripts/fix_test_markers.py

# 3. Check specific files
poetry run python scripts/verify_test_markers.py --changed

# 4. Manual fix for individual tests
# Add @pytest.mark.fast, @pytest.mark.medium, or @pytest.mark.slow
```

#### Problem: BDD Tests Failing
**Symptoms**: Feature files not found or step definitions not working
**Solutions**:
```bash
# 1. Verify feature file syntax
poetry run python -m pytest_bdd.check tests/behavior/features/

# 2. Generate step definition stubs
poetry run python scripts/generate_step_stubs.py tests/behavior/features/

# 3. Run BDD tests specifically
poetry run pytest tests/behavior/ -v

# 4. Check step definitions exist
find tests/behavior/steps -name "*steps.py" | head -5
```

### Platform-Specific Issues

#### macOS Issues
```bash
# Problem: Homebrew Python conflicts
# Solution: Use full path for Poetry environment
poetry env use /opt/homebrew/bin/python3.12

# Problem: ARM64 compatibility issues
# Solution: Some packages may not work on M1/M2 Macs
poetry install --with dev --extras "tests api"  # Skip problematic extras
```

#### Linux Issues
```bash
# Problem: System Python conflicts
# Solution: Use python3.12 explicitly
poetry env use python3.12

# Problem: Missing system dependencies
# Solution: Install build tools
sudo apt install build-essential python3.12-dev
```

#### Windows Issues
```bash
# Problem: Long path issues
# Solution: Enable long paths in Windows
# Or use WSL2 for development

# Problem: Line ending issues
# Solution: Configure Git for Windows
git config core.autocrlf false
```

### Performance Issues

#### Problem: Cursor IDE Slow or Unresponsive
**Solutions**:
```bash
# 1. Check context management settings in modes.json
# 2. Reduce max_files in global_settings
# 3. Exclude unnecessary directories in exclude_patterns
# 4. Restart Cursor IDE and clear cache
```

#### Problem: Tests Running Slowly
**Solutions**:
```bash
# 1. Use appropriate speed markers
poetry run devsynth run-tests --speed=fast

# 2. Run tests in parallel
poetry run pytest -n auto tests/unit/

# 3. Skip slow tests during development
poetry run pytest -m "not slow" tests/
```

### Validation

Run the comprehensive validation script:
```bash
poetry run python scripts/verify_cursor_integration.py
```

Run individual validation scripts:
```bash
# Test markers
poetry run python scripts/verify_test_markers.py

# Requirements traceability
poetry run python scripts/verify_requirements_traceability.py

# Environment validation
poetry run python scripts/check_dev_environment.py

# Poetry build validation
poetry run python scripts/verify_poetry_build.py
```

### Getting Help

1. **Check Documentation**: Review `docs/developer_guides/cursor_integration.md`
2. **Run Diagnostics**: Use `scripts/doctor/` directory for environment diagnostics
3. **Community Support**: Check project issues and discussions
4. **Environment Report**: Generate diagnostic report with `poetry run python scripts/diagnostics.sh`

## Next Steps

1. **Read the Rules**: Review `.cursor/rules` for comprehensive development guidance
2. **Practice BDD**: Try the specification-first workflow on a small feature
3. **Test Integration**: Run the integration tests and validation scripts
4. **Quality Checks**: Ensure all pre-commit hooks and validation scripts pass
5. **Explore Modes**: Try different Cursor modes for various development tasks

## Success Metrics

Your Cursor IDE integration is working correctly when:

✅ **Environment**: `poetry run python --version` shows Python 3.12.x from `.venv`
✅ **Integration**: `poetry run python scripts/verify_cursor_integration.py` passes all checks
✅ **Rules**: Cursor shows rule indicators and provides guided assistance
✅ **Commands**: Chat interface recognizes `/expand-phase`, `/generate-specification`, etc.
✅ **Testing**: `poetry run devsynth run-tests --speed=fast` runs successfully
✅ **Quality**: All pre-commit hooks and validation scripts pass

## Support and Resources

### Documentation
- **Cursor Integration Guide**: `docs/developer_guides/cursor_integration.md`
- **Project Constitution**: `constitution.md`
- **Development Policies**: `docs/policies/`
- **API Reference**: `docs/api_reference.md`

### Scripts and Tools
- **Integration Validation**: `scripts/verify_cursor_integration.py`
- **Environment Diagnostics**: `scripts/check_dev_environment.py`
- **Test Verification**: `scripts/verify_test_markers.py`
- **Requirements Traceability**: `scripts/verify_requirements_traceability.py`

### Community and Issues
- **Issue Tracker**: `issues/` directory for project-specific issues
- **Discussions**: Check project discussions for Cursor IDE topics
- **Contributing**: See `CONTRIBUTING.md` for development workflow

### Getting Help
1. **Run Diagnostics**: Use validation scripts to identify issues
2. **Check Documentation**: Review guides and policies
3. **Verify Environment**: Ensure Poetry environment is active
4. **Test Integration**: Confirm Cursor IDE is properly configured

## Best Practices Summary

1. **Always Use Poetry Environment**: `poetry run` prefix for all Python commands
2. **Follow EDRR Process**: Use Cursor commands for systematic development
3. **Specification First**: Check `docs/specifications/` before implementing
4. **Test-Driven Development**: Write failing tests before implementation
5. **Quality Gates**: Run validation scripts before committing
6. **Platform Consistency**: Use consistent environment setup across team

---

**🎉 Welcome to DevSynth + Cursor IDE Integration!**

This setup provides a comprehensive development environment that combines the power of Cursor IDE's AI assistance with DevSynth's structured methodologies. The integration ensures consistent quality, maintains architectural standards, and enhances developer productivity through guided workflows.

For questions or issues, start with the validation scripts and troubleshooting guides above.
