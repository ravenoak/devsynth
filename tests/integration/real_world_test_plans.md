# DevSynth Real-World Test Plans

**Author**: DevSynth Testing Team
**Date**: 2024-09-24
**Version**: v0.1.0a1
**Status**: Ready for Execution

## Overview

This document contains comprehensive test plans for validating DevSynth's end-to-end functionality through real-world application development scenarios. Each test case simulates a complete user journey from project initialization to working application deployment.

## Test Environment Setup

### Prerequisites
```bash
# Method 1: Using Poetry from DevSynth project directory (RECOMMENDED for v0.1.0a1)
cd /path/to/devsynth/project
poetry install --with dev --extras "tests retrieval chromadb api"
poetry run devsynth doctor  # Validate environment
poetry run devsynth --help  # Confirm CLI accessibility

# Method 2: Using direct venv path (RECOMMENDED for external directory execution)
DEVSYNTH_PROJECT="/path/to/devsynth"  # Adjust to your DevSynth location
DEVSYNTH_VENV="$(cd $DEVSYNTH_PROJECT && poetry env info --path)"
$DEVSYNTH_VENV/bin/devsynth --help  # Test from any directory

# Method 3: Using pipx (TESTED but has dependency issues for v0.1.0a1)
# pipx install --python /opt/homebrew/bin/python3.12 --include-deps -e ".[tests,retrieval,chromadb,api]"
# Note: Still has transitive dependency resolution issues (missing toml, tinydb, etc.)
# Recommended for post-alpha releases when dependency packaging is improved
```

### **CRITICAL**: Execution Context for v0.1.0a1 ✅ RESOLVED
- **SOLUTION FOUND**: Direct venv path approach works perfectly from any directory
- **Test creation directories can be anywhere** - full flexibility achieved
- **Recommended approach**: Use `DEVSYNTH_VENV="$(cd /path/to/devsynth && poetry env info --path)"` then `$DEVSYNTH_VENV/bin/devsynth` from any directory
- **pipx approach**: Your suggested `--python --include-deps -e .` approach works for installation but has minor dependency resolution issues for complex DevSynth dependency tree

### Test Data Preparation
- Create isolated test directories for each scenario
- Ensure clean environment (no existing .devsynth directories)
- Set appropriate environment variables for offline testing

## Test Case 1: Task Management CLI Application

### Objective
Validate DevSynth's ability to create a complete task management CLI application with CRUD operations, data persistence, and user interaction.

### Application Requirements
- **Complexity**: Beyond Hello World, includes data modeling, persistence, CLI interface
- **Features**: Add, list, complete, delete tasks with priority levels and due dates
- **Technology**: Python CLI application with JSON file storage

### Detailed Test Steps

#### Step 1: Project Initialization
```bash
# User Action
mkdir devsynth_test_task_manager
cd devsynth_test_task_manager
poetry run devsynth init

# Expected User Inputs During Interaction
# - Project name: "Task Manager CLI"
# - Description: "A command-line task management application"
# - Primary language: "Python"
# - Project type: "CLI Application"

# Expected Outputs
# - .devsynth/project.yaml created
# - Basic project structure initialized
# - Configuration validation passes
```

**Validation Criteria:**
- [ ] `.devsynth/project.yaml` exists and contains correct project metadata
- [ ] Project structure follows DevSynth conventions
- [ ] No errors during initialization

#### Step 2: Requirements Definition
```bash
# User Action: Create requirements.md
cat > requirements.md << 'EOF'
# Task Manager CLI Requirements

## Core Functionality
- The system shall allow users to add new tasks with title, description, priority, and due date
- The system shall display a list of all tasks with their status and metadata
- The system shall allow users to mark tasks as completed
- The system shall allow users to delete tasks
- The system shall persist tasks between application runs using JSON storage

## Priority Levels
- The system shall support three priority levels: High, Medium, Low
- The system shall display tasks sorted by priority and due date

## User Interface
- The system shall provide a command-line interface with clear commands
- The system shall display helpful messages and error handling
- The system shall validate user input and provide feedback

## Data Persistence
- The system shall store tasks in a JSON file in the user's home directory
- The system shall handle file I/O errors gracefully
- The system shall maintain data integrity across sessions
EOF

# User Action: Generate specifications
poetry run devsynth spec --requirements-file requirements.md
```

**Expected User Interactions During Spec Generation:**
- DevSynth may prompt for clarification on:
  - "What command-line interface style do you prefer? (argparse, click, typer)"
  - "Should tasks have categories or tags?"
  - "What date format should be used for due dates?"

**User Responses:**
- Interface: "typer for modern CLI with good help text"
- Categories: "No, keep it simple with just priorities"
- Date format: "YYYY-MM-DD format"

**Validation Criteria:**
- [ ] `specs.md` file generated with detailed technical specifications
- [ ] Specifications include data models, CLI commands, and file storage format
- [ ] Error handling and validation requirements are specified

#### Step 3: Test Generation
```bash
# User Action: Generate tests from specifications
poetry run devsynth test --spec-file specs.md
```

**Expected User Interactions:**
- DevSynth may ask:
  - "What testing framework do you prefer? (pytest, unittest)"
  - "Should we include integration tests for file I/O?"
  - "What test coverage level are you targeting?"

**User Responses:**
- Framework: "pytest for better fixtures and parametrization"
- Integration tests: "Yes, include file I/O tests with temporary files"
- Coverage: "Aim for 85% coverage with focus on business logic"

**Validation Criteria:**
- [ ] `tests/` directory created with comprehensive test suite
- [ ] Unit tests for task model, CLI commands, and storage operations
- [ ] Integration tests for end-to-end workflows
- [ ] Test fixtures and mock data appropriately configured

#### Step 4: Code Implementation
```bash
# User Action: Generate implementation code
poetry run devsynth code
```

**Expected User Interactions:**
- DevSynth may prompt:
  - "Should we create a package structure or single module?"
  - "What configuration format for the JSON storage location?"
  - "Should we include logging for debugging?"

**User Responses:**
- Structure: "Package structure with separate modules for models, CLI, and storage"
- Config: "Use ~/.task_manager/tasks.json as default, allow override via environment variable"
- Logging: "Include basic logging to help with debugging"

**Validation Criteria:**
- [ ] Source code generated in appropriate directory structure
- [ ] Code follows Python best practices and includes proper error handling
- [ ] All specified functionality implemented
- [ ] Code passes the generated tests

#### Step 5: Project Execution and Validation
```bash
# User Action: Run the generated application
poetry run devsynth run-pipeline

# Expected to install dependencies and run tests
# Then demonstrate the working application
```

**Expected User Interactions During Demo:**
- DevSynth may ask: "Would you like to run a demonstration of the task manager?"
- User response: "Yes, show me the basic functionality"

**Demo Sequence:**
1. Add a high-priority task: "Complete project documentation"
2. Add a medium-priority task: "Review code changes"
3. List all tasks
4. Mark first task as completed
5. List tasks again to show completion
6. Delete the completed task
7. Show final task list

**Validation Criteria:**
- [ ] Application installs and runs without errors
- [ ] All CRUD operations work correctly
- [ ] Data persists between application runs
- [ ] CLI interface is user-friendly with proper help text
- [ ] Error handling works for invalid inputs
- [ ] Generated tests pass with good coverage

### Expected Final Deliverables
- Working Python CLI application with typer interface
- Comprehensive test suite with >85% coverage
- JSON-based persistence layer
- Clear documentation and usage instructions
- Proper error handling and input validation

---

## Test Case 2: Personal Finance Tracker Web API

### Objective
Validate DevSynth's ability to create a RESTful web API for personal finance tracking with database integration, authentication, and data visualization endpoints.

### Application Requirements
- **Complexity**: Multi-tier web application with API, database, and basic frontend
- **Features**: Expense tracking, budget management, financial reports, user authentication
- **Technology**: FastAPI with SQLite database and basic HTML dashboard

### Detailed Test Steps

#### Step 1: Project Initialization
```bash
# User Action
mkdir devsynth_test_finance_tracker
cd devsynth_test_finance_tracker
poetry run devsynth init
```

**Expected User Inputs:**
- Project name: "Personal Finance Tracker API"
- Description: "RESTful API for tracking personal expenses and budgets"
- Primary language: "Python"
- Project type: "Web API"
- Framework preference: "FastAPI"

#### Step 2: Requirements Definition
```bash
cat > requirements.md << 'EOF'
# Personal Finance Tracker API Requirements

## Core Functionality
- The system shall provide REST endpoints for managing financial transactions
- The system shall support expense categories (food, transport, entertainment, utilities)
- The system shall track income and expense transactions with timestamps
- The system shall calculate running balances and category summaries
- The system shall provide monthly and yearly financial reports

## Data Management
- The system shall persist data in SQLite database with proper schema
- The system shall validate all financial data for accuracy and completeness
- The system shall support basic user authentication with API keys
- The system shall handle concurrent access safely

## API Endpoints
- POST /transactions - Add new income/expense transaction
- GET /transactions - List transactions with filtering options
- GET /balance - Get current account balance
- GET /categories/{category}/summary - Get spending summary by category
- GET /reports/monthly - Generate monthly financial report

## Security & Validation
- The system shall validate all monetary amounts are positive numbers
- The system shall require authentication for all endpoints
- The system shall sanitize input data to prevent injection attacks
- The system shall provide clear error messages for invalid requests

## Dashboard
- The system shall serve a simple HTML dashboard showing key metrics
- The system shall display recent transactions and balance information
- The system shall show spending by category in a simple chart
EOF

poetry run devsynth spec --requirements-file requirements.md
```

**Expected User Interactions:**
- "What database schema design do you prefer? (SQLAlchemy ORM, raw SQL)"
- "Should we include data export functionality?"
- "What authentication method? (API keys, JWT tokens, basic auth)"

**User Responses:**
- Schema: "SQLAlchemy ORM for easier maintenance and migrations"
- Export: "Yes, add CSV export for transactions"
- Auth: "API keys for simplicity in this demo"

#### Step 3: Test Generation
```bash
poetry run devsynth test --spec-file specs.md
```

**Expected User Interactions:**
- "Should we include API integration tests with test database?"
- "What test data should we generate for realistic scenarios?"
- "Should we test the HTML dashboard rendering?"

**User Responses:**
- Integration tests: "Yes, use in-memory SQLite for fast testing"
- Test data: "Generate sample transactions across different categories and time periods"
- Dashboard tests: "Basic tests to ensure HTML renders correctly"

#### Step 4: Code Implementation
```bash
poetry run devsynth code
```

**Expected User Interactions:**
- "Should we include database migration scripts?"
- "What port should the API server run on?"
- "Should we include CORS support for frontend integration?"

**User Responses:**
- Migrations: "Yes, include Alembic migrations for database versioning"
- Port: "8000 for development, configurable via environment"
- CORS: "Yes, enable CORS for local frontend development"

#### Step 5: Project Execution
```bash
poetry run devsynth run-pipeline
```

**Demo Sequence:**
1. Start the API server
2. Create sample transactions via API calls
3. Query balance and transaction endpoints
4. Generate monthly report
5. View HTML dashboard in browser
6. Test error handling with invalid data

**Validation Criteria:**
- [ ] FastAPI server starts and serves all endpoints
- [ ] Database schema creates correctly
- [ ] All CRUD operations work via REST API
- [ ] Authentication protects endpoints appropriately
- [ ] HTML dashboard displays financial data
- [ ] API documentation auto-generated and accessible
- [ ] Tests pass with good coverage of API endpoints

### Expected Final Deliverables
- Working FastAPI application with SQLite backend
- Complete REST API with authentication
- HTML dashboard for data visualization
- Database migrations and schema management
- Comprehensive test suite including API integration tests
- API documentation via FastAPI's automatic docs

---

## Test Case 3: File Organizer Desktop Utility

### Objective
Validate DevSynth's ability to create a desktop utility application with GUI interface, file system operations, and configuration management.

### Application Requirements
- **Complexity**: Desktop application with GUI, file operations, and user preferences
- **Features**: Automatic file organization by type/date, duplicate detection, batch operations
- **Technology**: Python with tkinter GUI and file system monitoring

### Detailed Test Steps

#### Step 1: Project Initialization
```bash
mkdir devsynth_test_file_organizer
cd devsynth_test_file_organizer
poetry run devsynth init
```

**Expected User Inputs:**
- Project name: "Smart File Organizer"
- Description: "Desktop utility for automatic file organization and duplicate detection"
- Primary language: "Python"
- Project type: "Desktop Application"
- GUI framework: "tkinter"

#### Step 2: Requirements Definition
```bash
cat > requirements.md << 'EOF'
# Smart File Organizer Requirements

## Core Functionality
- The system shall monitor specified directories for new files
- The system shall organize files by type into predefined folder structures
- The system shall detect and handle duplicate files with user confirmation
- The system shall support batch operations on multiple files
- The system shall maintain a log of all file operations for audit purposes

## File Organization Rules
- The system shall sort images by date taken (EXIF data) into YYYY/MM folders
- The system shall organize documents by file type (PDF, DOC, TXT, etc.)
- The system shall handle media files (video, audio) into appropriate directories
- The system shall preserve original timestamps during file moves

## User Interface
- The system shall provide a GUI for configuring organization rules
- The system shall display real-time progress during batch operations
- The system shall show preview of planned file moves before execution
- The system shall allow users to undo recent file operations

## Configuration Management
- The system shall save user preferences and folder mappings
- The system shall allow custom organization rules and file type mappings
- The system shall support multiple organization profiles
- The system shall validate directory permissions before operations

## Safety Features
- The system shall create backups before destructive operations
- The system shall handle file conflicts gracefully with user options
- The system shall validate file integrity after moves
- The system shall respect system file locks and permissions
EOF

poetry run devsynth spec --requirements-file requirements.md
```

**Expected User Interactions:**
- "Should we include a system tray icon for background monitoring?"
- "What file types should be supported for metadata extraction?"
- "Should we include file preview capabilities?"

**User Responses:**
- System tray: "Yes, allow background operation with system tray icon"
- File types: "Focus on common types: images (JPEG, PNG), documents (PDF, DOC), media (MP4, MP3)"
- Preview: "Basic file info preview, not full content preview"

#### Step 3: Test Generation and Implementation
```bash
poetry run devsynth test --spec-file specs.md
poetry run devsynth code
```

**Expected User Interactions:**
- "Should we include tests for file system operations with temporary directories?"
- "How should we handle GUI testing? (unit tests for logic, manual testing for UI)"
- "Should we include performance tests for large file operations?"

**User Responses:**
- File system tests: "Yes, use temporary directories and mock file operations"
- GUI testing: "Unit tests for business logic, separate manual test procedures for GUI"
- Performance: "Include basic performance tests with configurable file counts"

#### Step 4: Execution and Validation
```bash
poetry run devsynth run-pipeline
```

**Demo Sequence:**
1. Launch GUI application
2. Configure source and target directories
3. Set up organization rules for different file types
4. Run batch organization on sample files
5. Test duplicate detection with intentionally duplicated files
6. Demonstrate undo functionality
7. Show operation log and audit trail

**Validation Criteria:**
- [ ] GUI application launches and displays correctly
- [ ] File organization rules work accurately
- [ ] Duplicate detection identifies matches correctly
- [ ] Batch operations complete without data loss
- [ ] Configuration saves and loads properly
- [ ] Undo functionality restores previous state
- [ ] Operation logging provides complete audit trail

### Expected Final Deliverables
- Working desktop application with tkinter GUI
- File system monitoring and organization engine
- Configuration management system
- Comprehensive logging and audit capabilities
- Test suite covering file operations and business logic
- User manual and configuration guide

---

## Test Execution Framework

### Automated Test Execution
```bash
#!/bin/bash
# Real-world test execution script

# Test Case 1: Task Manager CLI
echo "=== Executing Test Case 1: Task Manager CLI ==="
cd /tmp
mkdir -p devsynth_tests/task_manager
cd devsynth_tests/task_manager
# ... execute test steps with validation

# Test Case 2: Finance Tracker API
echo "=== Executing Test Case 2: Finance Tracker API ==="
cd /tmp
mkdir -p devsynth_tests/finance_tracker
cd devsynth_tests/finance_tracker
# ... execute test steps with validation

# Test Case 3: File Organizer
echo "=== Executing Test Case 3: File Organizer ==="
cd /tmp
mkdir -p devsynth_tests/file_organizer
cd devsynth_tests/file_organizer
# ... execute test steps with validation
```

### Success Criteria for All Test Cases

#### Technical Validation
- [ ] All generated code compiles and runs without errors
- [ ] Generated tests achieve >80% code coverage
- [ ] Applications demonstrate specified functionality correctly
- [ ] Error handling works appropriately for edge cases
- [ ] Generated documentation is accurate and helpful

#### User Experience Validation
- [ ] DevSynth interactions are intuitive and well-guided
- [ ] Generated applications have appropriate user interfaces
- [ ] Installation and setup procedures work smoothly
- [ ] Generated code follows language-specific best practices
- [ ] Applications are maintainable and well-structured

#### EDRR Methodology Validation
- [ ] **Expand**: Requirements are properly analyzed and expanded into comprehensive specifications
- [ ] **Differentiate**: Generated solutions appropriately differentiate between different approaches and choose optimal ones
- [ ] **Refine**: Code and tests are refined through multiple iterations to meet quality standards
- [ ] **Retrospect**: Generated applications include proper logging, monitoring, and improvement suggestions

### Test Reporting

Each test case execution should generate:
1. **Execution Log**: Complete transcript of user interactions and DevSynth responses
2. **Generated Artifacts**: All files created during the test (code, tests, docs, configs)
3. **Validation Report**: Checklist results and any issues encountered
4. **Performance Metrics**: Time taken for each phase, resource usage
5. **User Experience Notes**: Observations about interaction quality and usability

### Integration with DevSynth Test Suite

These real-world test plans should be:
- Integrated into the CI/CD pipeline as extended integration tests
- Executed regularly to validate end-to-end functionality
- Used for regression testing when core components change
- Referenced for user acceptance testing and demo scenarios
- Maintained and updated as DevSynth capabilities evolve

---

**Note**: These test plans validate DevSynth's core value proposition: transforming requirements into working applications through an AI-driven EDRR methodology. Success in these scenarios demonstrates DevSynth's readiness for real-world usage by developers and teams.
