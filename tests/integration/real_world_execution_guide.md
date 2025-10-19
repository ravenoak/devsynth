# DevSynth Real-World Test Execution Guide

**Author**: DevSynth Testing Team
**Date**: 2024-09-24
**Version**: v0.1.0a1
**Purpose**: Provide step-by-step execution instructions for real-world DevSynth testing

## Quick Start

### Run All Real-World Tests
```bash
# From DevSynth project root
poetry run pytest tests/integration/test_real_world_scenarios.py -v --no-cov
```

### Run Individual Test Cases
```bash
# Task Manager CLI test
poetry run pytest tests/integration/test_real_world_scenarios.py::TestRealWorldScenarios::test_task_manager_cli_workflow -v

# Finance Tracker API test
poetry run pytest tests/integration/test_real_world_scenarios.py::TestRealWorldScenarios::test_finance_tracker_api_workflow -v

# File Organizer GUI test
poetry run pytest tests/integration/test_real_world_scenarios.py::TestRealWorldScenarios::test_file_organizer_gui_workflow -v
```

## Manual Test Execution

For comprehensive validation, execute these scenarios manually to experience the full user journey:

### Manual Test 1: Task Manager CLI

#### Setup
```bash
# IMPORTANT: DevSynth commands must be run from the DevSynth project directory for v0.1.0a1
# Create test directory but execute DevSynth from the project root

# Step 1: Set up test directory
mkdir /tmp/devsynth_manual_test_task_manager
TEST_DIR="/tmp/devsynth_manual_test_task_manager"

# Step 2: Get DevSynth project path (adjust as needed)
DEVSYNTH_PROJECT="/Users/caitlyn/Projects/github.com/ravenoak/devsynth"

# Step 3: Validate DevSynth is accessible
cd "$DEVSYNTH_PROJECT"
poetry run devsynth --help > /dev/null || {
    echo "ERROR: DevSynth not accessible from project directory"
    exit 1
}
```

#### Step-by-Step Execution

**Step 1: Initialize Project**
```bash
# Get DevSynth venv path (one-time setup)
cd "$DEVSYNTH_PROJECT"
DEVSYNTH_VENV="$(poetry env info --path)"

# Navigate to test directory and initialize
cd "$TEST_DIR"
echo -e "\n\npython\n\ny" | $DEVSYNTH_VENV/bin/devsynth init

# Alternative: Interactive mode
# $DEVSYNTH_VENV/bin/devsynth init
# Then provide inputs when prompted
```

**User Inputs to Provide:**
- When prompted for project name: `Task Manager CLI`
- When prompted for description: `A command-line task management application with priority levels and persistence`
- When prompted for primary language: `Python`
- When prompted for project type: `CLI Application`
- When prompted for additional features: `JSON persistence, priority levels, due dates`

**Expected Outcomes:**
- `.devsynth/project.yaml` created with correct metadata
- Basic project structure initialized
- No error messages during initialization

**Step 2: Create Requirements**
```bash
cat > requirements.md << 'EOF'
# Task Manager CLI Requirements

## Core Task Operations
- The system shall allow users to add new tasks with required title and optional description
- The system shall assign unique IDs to each task automatically
- The system shall allow users to list all tasks with their current status
- The system shall allow users to mark tasks as completed
- The system shall allow users to delete tasks by ID

## Priority Management
- The system shall support three priority levels: High, Medium, Low (default: Medium)
- The system shall display tasks sorted by priority (High first) then by creation date
- The system shall allow users to update task priority after creation

## Due Date Handling
- The system shall allow optional due dates in YYYY-MM-DD format
- The system shall highlight overdue tasks in the task list
- The system shall sort tasks by due date within priority groups

## Data Persistence
- The system shall store tasks in JSON format in ~/.task_manager/tasks.json
- The system shall create the storage directory automatically if it doesn't exist
- The system shall handle file I/O errors gracefully with informative messages
- The system shall maintain data integrity across application sessions

## Command Line Interface
- The system shall provide intuitive commands: add, list, complete, delete, update
- The system shall display helpful usage information with --help flag
- The system shall validate user input and provide clear error messages
- The system shall use colors and formatting for better readability

## Error Handling
- The system shall validate task IDs exist before operations
- The system shall prevent deletion of non-existent tasks
- The system shall handle corrupted JSON files gracefully
- The system shall provide recovery suggestions for common errors
EOF
```

**Step 3: Generate Specifications**
```bash
poetry run devsynth spec --requirements-file requirements.md
```

**Expected DevSynth Interactions:**
- DevSynth analyzes requirements and may ask clarifying questions
- Example prompts and suggested responses:

**Potential DevSynth Question**: "I see you want a CLI application with JSON persistence. Should we use a specific CLI framework?"
**Suggested User Response**: "Use Typer for modern Python CLI with automatic help generation and type validation"

**Potential DevSynth Question**: "For the priority sorting, should completed tasks be shown separately or mixed with active tasks?"
**Suggested User Response**: "Show completed tasks at the bottom, separated from active tasks, with a different visual indicator"

**Potential DevSynth Question**: "What should happen when the JSON file is corrupted or missing?"
**Suggested User Response**: "Create a backup of corrupted files and start with an empty task list, showing a warning message to the user"

**Expected Outcomes:**
- `specs.md` file created with detailed technical specifications
- Specifications include data models, CLI command structure, and storage format
- Error handling scenarios clearly defined
- User interface specifications with command examples

**Step 4: Generate Tests**
```bash
poetry run devsynth test --spec-file specs.md
```

**Expected DevSynth Interactions:**

**Potential DevSynth Question**: "Should we include integration tests for the JSON file operations?"
**Suggested User Response**: "Yes, include integration tests using temporary directories to test file I/O without affecting the user's actual data"

**Potential DevSynth Question**: "What level of test coverage should we target for this application?"
**Suggested User Response**: "Target 85% coverage focusing on business logic, with comprehensive testing of error conditions and edge cases"

**Potential DevSynth Question**: "Should we include performance tests for large task lists?"
**Suggested User Response**: "Include basic performance tests to ensure the application handles up to 1000 tasks efficiently"

**Expected Outcomes:**
- `tests/` directory with comprehensive test suite
- Unit tests for task model, CLI commands, and storage operations
- Integration tests for end-to-end workflows with temporary files
- Mock data and fixtures for testing various scenarios

**Step 5: Generate Implementation**
```bash
poetry run devsynth code
```

**Expected DevSynth Interactions:**

**Potential DevSynth Question**: "Should we create a package structure or keep everything in a single module?"
**Suggested User Response**: "Create a package structure with separate modules: models.py for data classes, cli.py for command interface, storage.py for persistence, and main.py for entry point"

**Potential DevSynth Question**: "What should be the default behavior when no tasks exist?"
**Suggested User Response**: "Display a friendly message suggesting how to add the first task, with an example command"

**Potential DevSynth Question**: "Should we include configuration options for the storage location?"
**Suggested User Response**: "Yes, allow override via TASK_MANAGER_DATA_DIR environment variable, but default to ~/.task_manager/"

**Expected Outcomes:**
- Complete Python package with proper structure
- All CLI commands implemented with Typer
- JSON storage system with error handling
- Type hints and docstrings throughout
- Proper logging configuration

**Step 6: Run and Validate**
```bash
poetry run devsynth run-pipeline
```

**Manual Validation Steps:**
1. **Test Installation**: Verify the application can be installed and imported
2. **Test CLI Help**: Run `python -m task_manager --help` to see command options
3. **Test Add Command**: Add several tasks with different priorities and due dates
4. **Test List Command**: Verify tasks display correctly with proper sorting
5. **Test Complete Command**: Mark tasks as completed and verify status changes
6. **Test Delete Command**: Remove tasks and verify they're gone
7. **Test Persistence**: Exit and restart application, verify data persists
8. **Test Error Handling**: Try invalid commands and verify helpful error messages

**Expected Final Validation:**
- [ ] All CLI commands work as specified
- [ ] Data persists correctly between sessions
- [ ] Error messages are helpful and actionable
- [ ] Task sorting works correctly (priority then date)
- [ ] File I/O errors are handled gracefully
- [ ] Generated tests pass with good coverage
- [ ] Code follows Python best practices

---

### Manual Test 2: Finance Tracker API

#### Setup
```bash
mkdir /tmp/devsynth_manual_test_finance_api
cd /tmp/devsynth_manual_test_finance_api
```

**Follow similar detailed steps as Test 1, but with API-specific validations:**

#### Key Differences in User Interactions

**During Init:**
- Project type: `Web API`
- Framework: `FastAPI with SQLAlchemy`
- Database: `SQLite for development`

**During Spec Generation:**
- API design: `RESTful with proper HTTP status codes`
- Authentication: `API key based authentication`
- Data validation: `Pydantic models for request/response validation`

**During Test Generation:**
- Test framework: `pytest with FastAPI TestClient`
- Database testing: `In-memory SQLite for fast tests`
- API testing: `Full request/response cycle testing`

**During Code Generation:**
- Database migrations: `Include Alembic for schema versioning`
- API documentation: `Auto-generated OpenAPI docs`
- Error handling: `Proper HTTP error responses with details`

#### API-Specific Validation Steps
1. **Start API Server**: `uvicorn main:app --reload`
2. **Test Endpoints**: Use curl or httpie to test all endpoints
3. **Validate OpenAPI Docs**: Check `/docs` endpoint for API documentation
4. **Test Authentication**: Verify API key protection works
5. **Test Database Operations**: Verify data persists correctly
6. **Test Error Responses**: Validate proper HTTP status codes and error messages

---

### Manual Test 3: File Organizer GUI

#### Setup
```bash
mkdir /tmp/devsynth_manual_test_file_organizer
cd /tmp/devsynth_manual_test_file_organizer
```

#### Key Differences in User Interactions

**During Init:**
- Project type: `Desktop Application`
- GUI framework: `tkinter (built-in) for maximum compatibility`
- Features: `File monitoring, duplicate detection, undo functionality`

**During Spec Generation:**
- GUI layout: `Simple tabbed interface with configuration and operation panels`
- File operations: `Safe file moves with confirmation dialogs`
- Configuration: `User-customizable organization rules`

**During Test Generation:**
- GUI testing: `Unit tests for business logic, manual procedures for GUI`
- File operations: `Use temporary directories for safe testing`
- Mock testing: `Mock file system operations for unit tests`

#### GUI-Specific Validation Steps
1. **Launch Application**: Verify GUI opens without errors
2. **Configure Directories**: Set source and target directories
3. **Test File Operations**: Create sample files and test organization
4. **Test Duplicate Detection**: Create duplicate files and verify detection
5. **Test Undo Functionality**: Verify file moves can be reversed
6. **Test Configuration Persistence**: Verify settings save between sessions

## Automated Test Execution Script

Create this script for automated execution of all scenarios:

```bash
#!/bin/bash
# File: scripts/run_real_world_tests.sh

set -e

echo "=== DevSynth Real-World Test Execution ==="
echo "Date: $(date)"
echo "Environment: $(poetry env info --path)"

# Ensure DevSynth is available
echo "Validating DevSynth installation..."
poetry run devsynth --help > /dev/null || {
    echo "ERROR: DevSynth CLI not available"
    exit 1
}

# Run integration tests
echo "Running automated real-world scenario tests..."
poetry run pytest tests/integration/test_real_world_scenarios.py -v --tb=short

# Generate execution report
echo "Generating test execution report..."
poetry run pytest tests/integration/test_real_world_scenarios.py --html=test_reports/real_world_tests.html --self-contained-html

echo "=== Real-World Tests Complete ==="
echo "Report available at: test_reports/real_world_tests.html"
```

## Success Criteria Summary

### Technical Validation
- [ ] All test cases execute without errors
- [ ] Generated applications demonstrate specified functionality
- [ ] Code quality meets project standards
- [ ] Test coverage exceeds 80% for generated code
- [ ] Error handling works appropriately

### User Experience Validation
- [ ] DevSynth interactions are intuitive and well-guided
- [ ] Generated applications have appropriate user interfaces
- [ ] Installation and setup procedures work smoothly
- [ ] Documentation is clear and helpful
- [ ] Applications are maintainable and extensible

### EDRR Methodology Validation
- [ ] **Expand**: Requirements properly analyzed and expanded
- [ ] **Differentiate**: Optimal solutions selected from alternatives
- [ ] **Refine**: Code quality improved through iterations
- [ ] **Retrospect**: Learning captured for future improvements

## Integration with CI/CD

Add these tests to the DevSynth CI pipeline:

```yaml
# .github/workflows/real_world_tests.yml (when workflows are re-enabled)
name: Real-World Scenario Tests

on:
  workflow_dispatch:  # Manual trigger only until v0.1.0a1 tag

jobs:
  real-world-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install --with dev --extras "tests retrieval chromadb api"
      - name: Run real-world tests
        run: poetry run pytest tests/integration/test_real_world_scenarios.py -v
      - name: Upload test artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: real-world-test-artifacts
          path: test_reports/
```

---

**Note**: These test plans validate DevSynth's core value proposition by simulating realistic development scenarios that demonstrate the platform's ability to transform requirements into working applications through the EDRR methodology.
