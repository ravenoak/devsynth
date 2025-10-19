# Testing Configuration Guide

## Overview

This guide documents the consolidated and simplified testing configuration for DevSynth, implemented as part of the testing infrastructure evaluation and improvement effort.

## Key Principles

1. **Unified Configuration**: Single source of truth for coverage and test settings
2. **Clear Categorization**: Well-organized test markers without duplication
3. **Simplified Isolation**: Streamlined test isolation without over-engineering
4. **Maintainable Scripts**: Consolidated testing automation with clear interfaces

## Configuration Files

### pytest.ini

The main pytest configuration file defines:

- **Test discovery**: `testpaths = tests`
- **Default options**: Coverage reporting, marker filtering
- **Marker definitions**: Organized by category (resource, speed, type, context, functional)

Key settings:
```ini
addopts = -p no:benchmark --cov=src/devsynth --cov-report=term-missing:skip-covered \
          --cov-report=json:test_reports/coverage.json --cov-fail-under=90 \
          -m "not slow and not gui and not memory_intensive" --strict-markers --strict-config -ra
```

### .coveragerc

Unified coverage configuration replacing multiple specialized configs:

- **Source**: `src/devsynth`
- **Threshold**: 90% aggregate coverage (default). Use
  `DEVSYNTH_COV_FAIL_UNDER` or append `--cov-fail-under=<value>` for focused
  smoke/debugging runs when intentionally bypassing the release gate.
- **Reports**: Terminal (per-file percentages via `term-missing:skip-covered`), HTML, XML, JSON. For a full module inventory that
  includes files hidden by `skip-covered`, refresh `diagnostics/devsynth_coverage_per_file_<timestamp>.txt` via
  `utils_coverage.json`.
- **Exclusions**: Standard boilerplate and unreachable code patterns

## Test Markers

### Speed Markers (Required)
Every test must have exactly one speed marker:
- `@pytest.mark.fast` - Execution time < 1s
- `@pytest.mark.medium` - Execution time 1-5s
- `@pytest.mark.slow` - Execution time > 5s

### Resource Markers
For tests requiring external dependencies:
- `@pytest.mark.requires_resource("chromadb")`
- `@pytest.mark.requires_resource("openai")`
- `@pytest.mark.requires_resource("lmstudio")`
- etc.

### Test Type Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.property` - Property-based tests

### Execution Context Markers
- `@pytest.mark.isolation` - Must run separately
- `@pytest.mark.gui` - Requires GUI components
- `@pytest.mark.docker` - Requires Docker
- `@pytest.mark.memory_intensive` - Uses significant memory

## Test Organization

### Directory Structure
```
tests/
├── unit/           # Unit tests (mirror src/ structure)
├── integration/    # Integration tests (by feature area)
├── behavior/       # BDD tests with .feature files
├── performance/    # Performance benchmarks
├── property/       # Property-based tests
└── fixtures/       # Shared test fixtures
```

### Naming Conventions
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature_name>_integration.py`
- BDD features: `<feature_name>.feature`
- Step definitions: `test_<feature_name>_steps.py`

## Running Tests

### Basic Commands
```bash
# All fast tests (default)
poetry run pytest

# All tests including slow ones
poetry run pytest -m "all"

# Specific speed category
poetry run pytest -m "fast"
poetry run pytest -m "medium"
poetry run pytest -m "slow"

# Specific test type
poetry run pytest -m "unit"
poetry run pytest -m "integration"

# With coverage report
poetry run pytest --cov-report=html

# Parallel execution
poetry run pytest -n auto
```

### DevSynth CLI Integration
```bash
# Recommended interface
poetry run devsynth run-tests --speed=fast
poetry run devsynth run-tests --target=unit-tests
poetry run devsynth run-tests --report
```

## Test Fixtures

### Global Isolation
The `global_test_isolation` fixture (autouse) provides:
- Temporary directories for all test artifacts
- Environment variable isolation
- Working directory restoration
- Global state reset

### Resource Fixtures
Available in `tests/fixtures/backends.py`:
- `chromadb_client` - Temporary ChromaDB instance
- `temp_kuzu_store` - Ephemeral Kuzu database
- `mock_lmstudio` - LM Studio API mock

### Determinism Fixtures
From `tests/fixtures/determinism.py`:
- `deterministic_seed` - Fixed RNG seeds
- `enforce_test_timeout` - Per-test timeouts

## Coverage Configuration

### Unified Approach
- Single `.coveragerc` file for all coverage measurement
- No specialized configurations for different modules
- Consistent 90% threshold across all contexts

### Reports Generated
- Terminal: Immediate feedback during test runs
- HTML: Detailed browsable report in `htmlcov/`
- XML: For CI/CD integration (`coverage.xml`)
- JSON: For programmatic analysis (`coverage.json`)

## Best Practices

### Writing Tests
1. **Always include exactly one speed marker**
2. **Use resource markers for external dependencies**
3. **Prefer unit tests over integration tests when possible**
4. **Mark isolation tests only when necessary**
5. **Follow naming conventions consistently**

### Test Isolation
1. **Use provided fixtures for temporary resources**
2. **Avoid setting environment variables at import time**
3. **Clean up resources in fixture teardown**
4. **Mock external services by default**

### Performance
1. **Minimize isolation-marked tests**
2. **Use parallel execution for independent tests**
3. **Prefer fast tests for rapid feedback**
4. **Profile slow tests to identify optimization opportunities**

## Troubleshooting

### Common Issues

**Missing Speed Markers**
```bash
# Verify all tests have speed markers
poetry run python scripts/verify_test_markers.py
```

**Coverage Issues**
```bash
# Check coverage configuration
poetry run pytest --cov-config --collect-only
```

**Resource Availability**
```bash
# Check which resources are available
poetry run devsynth doctor
```

**Isolation Test Failures**
```bash
# Run isolation tests separately
poetry run pytest -m isolation
```

### Debug Commands
```bash
# Collect tests without running
poetry run pytest --collect-only

# Show available markers
poetry run pytest --markers

# Verbose test discovery
poetry run pytest --collect-only -v

# Check fixture usage
poetry run pytest --fixtures
```

## Migration Notes

### From Previous Configuration
This consolidated configuration replaces:
- Multiple `.coveragerc*` files
- Duplicate marker definitions in pytest.ini
- Complex WebUI coverage patching
- Fragmented testing scripts

### Breaking Changes
- Coverage threshold unified at 90%
- Removed auto-injection of speed markers for BDD tests
- Simplified isolation fixture behavior
- Consolidated resource availability checking

### Upgrade Path
1. Update test files to use unified markers
2. Remove specialized coverage configurations
3. Use new `devsynth run-tests` interface
4. Update CI/CD to use consolidated configuration

## Future Improvements

Tracked in repository issues:
- Script consolidation and CLI interface improvements
- Test quality metrics and trend analysis
- Advanced parallel execution optimization
- Enhanced resource management

---

*This guide reflects the testing configuration as of the infrastructure consolidation effort. For implementation details, see the dialectical analysis in the repository's testing evaluation documentation.*
