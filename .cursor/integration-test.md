# Cursor Rules Integration Test

This document provides test scenarios to validate that the Cursor IDE rules enable effective LLM agent operation within DevSynth.

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

## Continuous Improvement

Monitor agent behavior and update rules when:

1. New failure patterns emerge
2. DevSynth workflows change
3. Additional tooling is introduced
4. Quality standards evolve
5. Security requirements change

The goal is continuous refinement to maximize agent effectiveness while maintaining DevSynth's high standards for quality, security, and process compliance.
