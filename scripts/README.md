# DevSynth Testing Scripts

This directory contains scripts for comprehensive testing of the DevSynth project. These scripts were created as part of the Phase 4 testing effort.

## Available Scripts

### 1. Run All Tests (`run_all_tests.py`)

This script executes all unit, integration, and behavior tests and generates a comprehensive report of the results.

```bash
# Run all tests
./scripts/run_all_tests.py

# Run only unit tests
./scripts/run_all_tests.py --unit

# Run only integration tests
./scripts/run_all_tests.py --integration

# Run only behavior tests
./scripts/run_all_tests.py --behavior

# Generate HTML report
./scripts/run_all_tests.py --report

# Show verbose output
./scripts/run_all_tests.py --verbose
```

### 2. Manual CLI Testing (`manual_cli_testing.py`)

This script guides you through manual testing of DevSynth CLI workflows and records the results.

```bash
# Run manual CLI testing
./scripts/manual_cli_testing.py

# Specify output file
./scripts/manual_cli_testing.py --output my_results.md
```

The script tests the following CLI commands:
- `devsynth help`
- `devsynth init`
- `devsynth spec`
- `devsynth test`
- `devsynth code`
- `devsynth run`
- `devsynth config`

### 3. WebUI Testing (`webui_testing.py`)

This script guides you through testing WebUI navigation and functionality and records the results.

```bash
# Run WebUI testing
./scripts/webui_testing.py

# Specify output file
./scripts/webui_testing.py --output my_results.md
```

The script tests the following WebUI features:
- Home page
- Project creation
- Requirements page
- Specifications page
- Test generation page
- Code generation page
- Project settings page
- Navigation flow
- Error handling
- Responsive design

### 4. Agent API Testing (`agent_api_testing.py`)

This script tests the Agent API endpoints with various clients and records the results.

```bash
# Run Agent API testing
./scripts/agent_api_testing.py

# Specify output file
./scripts/agent_api_testing.py --output my_results.md

# Specify host and port
./scripts/agent_api_testing.py --host localhost --port 8000
```

The script tests the following API endpoints:
- `/health`
- `/metrics`
- `/generate`
- `/analyze`

It also tests authentication, error handling, and rate limiting.

### 5. Configuration Testing (`config_testing.py`)

This script tests DevSynth with various configuration settings and records the results.

```bash
# Run configuration testing
./scripts/config_testing.py

# Specify output file
./scripts/config_testing.py --output my_results.md
```

The script tests the following configuration options:
- Default configuration
- Different LLM models (gpt-4, gpt-3.5-turbo, claude-3-opus)
- Different LLM providers (openai, anthropic, lmstudio)
- Different memory backends (simple, chromadb, faiss, kuzu)
- Different programming languages (python, javascript, java, go, rust)
- Different architecture styles (hexagonal, mvc, clean, microservices)
- Different test frameworks (pytest, unittest, jest, mocha, etc.)
- Environment variables
- Command line options
- Complex configuration with multiple settings

## Best Practices

These scripts follow these best practices:

1. **Proper Error Handling**: All scripts include comprehensive error handling to ensure they fail gracefully and provide useful error messages.

2. **Comprehensive Test Coverage**: The scripts cover a wide range of functionality, including edge cases and error conditions.

3. **Clear Documentation**: Each script includes detailed documentation, including usage instructions and examples.

4. **Proper Test Isolation**: The scripts use temporary directories and clean up after themselves to ensure tests don't interfere with each other or the user's environment.

5. **Consistent Coding Style**: All scripts follow a consistent coding style with proper docstrings, type hints, and naming conventions.

6. **Detailed Reporting**: All scripts generate detailed reports of test results, including pass/fail status, error messages, and other relevant information.

7. **Configurability**: All scripts provide command-line options for customizing their behavior.

## Usage in CI/CD

These scripts can be integrated into a CI/CD pipeline to ensure comprehensive testing of the DevSynth project. For example:

```yaml
# Example GitHub Actions workflow
name: Comprehensive Testing

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install
    - name: Run all tests
      run: |
        ./scripts/run_all_tests.py --report
    - name: Upload test report
      uses: actions/upload-artifact@v2
      with:
        name: test-report
        path: test_reports/
```

## Maintenance

These scripts should be maintained and updated as the DevSynth project evolves. If new features are added or existing features are modified, the corresponding tests should be updated accordingly.