# Cursor IDE Integration Testing and Debugging Guide

This comprehensive guide provides testing scenarios, debugging workflows, and validation procedures for Cursor IDE integration with DevSynth. It includes practical workflows for testing, debugging, and validating the integration in various development scenarios.

## Cursor IDE Testing Integration

### Terminal Integration Testing

**Testing Poetry Environment in Cursor Terminal:**
```bash
# 1. Verify Python version
poetry run python --version  # Should show 3.12.x from .venv

# 2. Test CLI functionality
poetry run devsynth --help

# 3. Run fast tests
poetry run devsynth run-tests --speed=fast

# 4. Check environment variables
poetry run python -c "import os; print(os.environ.get('DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE'))"
```

**Testing Cursor Commands:**
```bash
# Test EDRR workflow commands in Cursor chat
/expand-phase implement user authentication system
# Should generate multiple approaches with pros/cons

/differentiate-phase authentication security complexity performance
# Should provide structured comparison

/refine-phase implement OAuth2 with FastAPI Security
# Should generate implementation with tests

/retrospect-phase authentication implementation analysis
# Should capture learnings and improvements
```

**Testing Custom Modes:**
```bash
# Switch to different modes in Cursor and verify behavior

# EDRRImplementer Mode (Cmd+Shift+E)
# Should provide implementation-focused guidance

# SpecArchitect Mode (Cmd+Shift+S)
# Should provide specification and BDD guidance

# TestArchitect Mode (Cmd+Shift+T)
# Should provide testing-focused guidance
```

### Debugging Workflows

#### Environment Debugging
```bash
# 1. Check Poetry environment status
poetry env info
poetry env info --path

# 2. Verify virtual environment activation
poetry run which python  # Should show .venv/bin/python

# 3. Check installed packages
poetry run pip list | grep -E "(pytest|mypy|black|devsynth)"

# 4. Test import functionality
poetry run python -c "import devsynth; print('DevSynth import successful')"
```

#### Rule Application Debugging
```bash
# 1. Verify Cursor integration
poetry run python scripts/verify_cursor_integration.py

# 2. Check rule frontmatter
find .cursor/rules -name "*.mdc" -exec head -5 {} \;

# 3. Test rule validation
poetry run python .cursor/validate-rules.py

# 4. Verify command availability
ls -la .cursor/commands/
```

#### Testing Debugging
```bash
# 1. Check test markers
poetry run python scripts/verify_test_markers.py

# 2. Test specific categories
poetry run pytest tests/unit/ --collect-only -q
poetry run pytest tests/behavior/ --collect-only -q

# 3. Run tests with verbose output
poetry run pytest tests/unit/test_example.py -v -s

# 4. Debug failing tests
poetry run pytest tests/unit/test_example.py -v -s --tb=short
```

#### BDD Testing Integration
```bash
# 1. Validate feature files
poetry run python -m pytest_bdd.check tests/behavior/features/

# 2. Test step definitions
poetry run pytest tests/behavior/steps/ -v

# 3. Run BDD scenarios
poetry run pytest tests/behavior/features/example.feature -v

# 4. Generate step stubs (if needed)
poetry run python scripts/generate_step_stubs.py tests/behavior/features/
```

## Platform-Specific Testing

### macOS Testing Workflows
```bash
# 1. Verify Homebrew Python
/opt/homebrew/bin/python3.12 --version

# 2. Test Poetry environment
poetry env info --path  # Should show .venv

# 3. Run comprehensive tests
poetry install --with dev --extras "tests retrieval chromadb api"
poetry run devsynth run-tests --speed=fast

# 4. Test optional resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
poetry run pytest -m "requires_resource" --maxfail=3
```

### Linux Testing Workflows
```bash
# 1. Verify system Python
python3.12 --version

# 2. Test environment isolation
poetry run which python  # Should not be system Python

# 3. Run tests with available extras
poetry install --with dev --extras "tests chromadb api"
poetry run devsynth run-tests --speed=fast

# 4. Test platform-specific features
python -c "import platform; print(platform.machine(), platform.system())"
```

### Windows Testing Workflows
```bash
# 1. Verify Python installation
python --version

# 2. Test Poetry environment
poetry env info --path

# 3. Run basic tests (limited extras on Windows)
poetry install --with dev --extras "tests api"
poetry run devsynth run-tests --speed=fast

# 4. Test environment variables
set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
poetry run pytest -m "requires_resource" --maxfail=3
```

## Test Scenario 1: New Feature Development

**Objective**: Verify that an LLM agent can follow the complete BDD workflow for adding a new feature.

### Expected Agent Behavior:
1. Create specification in `docs/specifications/test_feature.md`
2. Create failing BDD test in `tests/behavior/features/test_feature.feature`
3. Create step definitions in `tests/behavior/steps/test_feature_steps.py`
4. Create unit tests with proper speed markers
5. Implement the feature in appropriate location
6. Verify all tests pass
7. Run quality checks
8. Resolve dialectical audit

### Validation Commands:
```bash
# After agent completes work, verify:
poetry run pytest tests/behavior/features/test_feature.feature
poetry run python scripts/verify_test_markers.py --changed
poetry run pre-commit run --all-files
poetry run python scripts/dialectical_audit.py
```

## Test Scenario 2: CLI Command Addition

**Objective**: Verify that an LLM agent can correctly add a new CLI command following DevSynth patterns.

### Expected Agent Behavior:
1. Create specification for the CLI command
2. Create BDD tests for CLI behavior
3. Implement command in `src/devsynth/application/cli/commands/`
4. Register command with CLI system
5. Create appropriate unit and integration tests
6. Use correct speed markers and resource flags

### Validation Commands:
```bash
# Verify CLI command is registered
poetry run devsynth --help | grep "new-command"

# Verify tests are properly structured
poetry run pytest tests/unit/application/cli/commands/test_new_command.py -v
poetry run pytest tests/integration/cli/test_new_command_integration.py -v
```

## Test Scenario 3: Memory Backend Integration

**Objective**: Verify that an LLM agent can add a new memory backend with proper resource flag integration.

### Expected Agent Behavior:
1. Create specification for memory backend
2. Create BDD tests with resource flags
3. Implement backend in `src/devsynth/application/memory/`
4. Create adapter if needed
5. Update pyproject.toml with optional dependency
6. Add resource flag configuration
7. Create comprehensive tests with proper markers

### Validation Commands:
```bash
# Verify resource flag integration
export DEVSYNTH_RESOURCE_NEWBACKEND_AVAILABLE=true
poetry run pytest -m "requires_resource('newbackend')" tests/integration/memory/

# Verify optional dependency handling
poetry install --extras newbackend
```

## Test Scenario 4: Security Compliance

**Objective**: Verify that an LLM agent maintains security and audit compliance throughout development.

### Expected Agent Behavior:
1. Follow security policies during implementation
2. Run security checks before committing
3. Resolve dialectical audit questions
4. Maintain proper documentation
5. Use secure coding practices

### Validation Commands:
```bash
# Verify security compliance
poetry run bandit -r src/devsynth
poetry run safety check
poetry run python scripts/dialectical_audit.py

# Verify no unresolved audit questions
test ! -s dialectical_audit.log || echo "Audit questions remain unresolved"
```

## Test Scenario 5: Quality Standards Adherence

**Objective**: Verify that an LLM agent maintains code quality standards automatically.

### Expected Agent Behavior:
1. Use proper type hints
2. Follow formatting standards
3. Maintain test coverage
4. Use conventional commits
5. Update documentation appropriately

### Validation Commands:
```bash
# Verify code quality
poetry run black --check .
poetry run isort --check-only .
poetry run flake8 src/ tests/
poetry run mypy src/ tests/

# Verify test coverage
poetry run devsynth run-tests --report --speed=fast
```

## Success Criteria

The Cursor rules are successful if LLM agents can:

1. **✅ Follow BDD Workflow**: Always create specifications and failing tests first
2. **✅ Maintain Test Discipline**: Use correct speed markers and resource flags
3. **✅ Use Proper Commands**: Always use `poetry run` and correct CLI patterns
4. **✅ Organize Files Correctly**: Place code in appropriate directories
5. **✅ Meet Quality Standards**: Pass all formatting, linting, and typing checks
6. **✅ Maintain Security**: Follow security policies and resolve audit questions
7. **✅ Integrate with Tooling**: Use task runner, CLI, and existing scripts properly
8. **✅ Document Changes**: Update specifications and documentation appropriately

## Failure Modes to Watch For

Common LLM agent mistakes that the rules should prevent:

1. **❌ Skipping BDD Workflow**: Implementing code without specifications/tests first
2. **❌ Missing Test Markers**: Tests without speed markers or incorrect markers
3. **❌ Wrong Command Usage**: Using bare `python` instead of `poetry run`
4. **❌ File Misplacement**: Creating files in wrong directories
5. **❌ Security Violations**: Ignoring security policies or audit requirements
6. **❌ Quality Issues**: Poor formatting, typing, or linting compliance
7. **❌ Tooling Ignorance**: Not using existing scripts and automation
8. **❌ Documentation Gaps**: Failing to update relevant documentation

## Integration Validation

### Comprehensive Integration Testing

**Full Integration Test Suite:**
```bash
# 1. Environment validation
poetry run python scripts/verify_cursor_integration.py

# 2. Environment setup validation
poetry run python scripts/check_dev_environment.py

# 3. Test markers validation
poetry run python scripts/verify_test_markers.py

# 4. Requirements traceability
poetry run python scripts/verify_requirements_traceability.py

# 5. Version synchronization
poetry run python scripts/verify_version_sync.py

# 6. Security audit
poetry run python scripts/dialectical_audit.py

# 7. Quality gates
poetry run pre-commit run --all-files
```

**Performance Testing:**
```bash
# 1. Test execution speed
time poetry run devsynth run-tests --speed=fast

# 2. Memory usage monitoring
poetry run python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# 3. Cursor responsiveness
# Test command response times in Cursor chat
```

**Cross-Platform Testing:**
```bash
# 1. Test on multiple platforms
# Run tests on macOS, Linux, and Windows environments

# 2. Platform-specific feature testing
poetry run python -c "
import platform
import sys
print(f'Platform: {platform.platform()}')
print(f'Python: {sys.version}')
print(f'Machine: {platform.machine()}')
"

# 3. Environment variable testing
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
poetry run pytest -m "requires_resource" --tb=short
```

### Cursor IDE Feature Testing

**Chat Interface Testing:**
```bash
# Test all EDRR commands
/expand-phase implement feature
/differentiate-phase approaches
/refine-phase implementation
/retrospect-phase analysis

# Test specification commands
/generate-specification feature
/validate-bdd-scenarios feature
/generate-test-suite component

# Test development commands
/fix-bdd-syntax feature
/add-speed-markers tests
/update-specifications implementation
```

**Composer Mode Testing:**
```bash
# Test code generation with Cursor composer
# 1. Open Cursor composer
# 2. Apply DevSynth rules
# 3. Generate code with tests
# 4. Verify quality compliance
```

**Context Management Testing:**
```bash
# Test context loading and awareness
# 1. Open project in Cursor
# 2. Verify rules are loaded
# 3. Test context-aware suggestions
# 4. Verify specification access
```

## Continuous Improvement

Monitor agent behavior and update integration when:

1. **New failure patterns emerge**: Update rules to prevent common mistakes
2. **DevSynth workflows change**: Modify commands and guidance accordingly
3. **Additional tooling is introduced**: Update integration scripts and validation
4. **Quality standards evolve**: Enhance quality gates and compliance checking
5. **Security requirements change**: Update security rules and validation
6. **Performance issues arise**: Optimize context management and rule application
7. **Platform compatibility changes**: Update platform-specific guidance

### Integration Metrics

**Success Metrics:**
- ✅ **Environment Setup**: 100% of validation scripts pass
- ✅ **Rule Application**: All core rules load and apply correctly
- ✅ **Command Availability**: All Cursor commands are recognized and functional
- ✅ **Testing Integration**: Tests run successfully in Cursor terminal
- ✅ **Quality Gates**: All pre-commit hooks and validation scripts pass
- ✅ **Cross-Platform**: Integration works on macOS, Linux, and Windows

**Performance Metrics:**
- ✅ **Setup Time**: Complete environment setup in <5 minutes
- ✅ **Test Execution**: Fast tests complete in <30 seconds
- ✅ **Rule Loading**: Cursor rules load in <2 seconds
- ✅ **Command Response**: Chat commands respond in <5 seconds

**Quality Metrics:**
- ✅ **Test Coverage**: Maintain >90% coverage with comprehensive testing
- ✅ **Security Compliance**: All security checks pass automatically
- ✅ **Code Quality**: All linting and formatting checks pass
- ✅ **Documentation**: All specifications and tests are properly documented

The goal is continuous refinement to maximize developer productivity while maintaining DevSynth's high standards for quality, security, and process compliance. Regular integration testing ensures the Cursor IDE integration remains effective and reliable across all supported platforms and development scenarios.
