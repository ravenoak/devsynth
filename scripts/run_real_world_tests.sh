#!/bin/bash
# DevSynth Real-World Test Execution Script
#
# This script executes comprehensive real-world scenarios to validate
# DevSynth's end-to-end functionality through complete application development workflows.
#
# Author: DevSynth Testing Team
# Date: 2024-09-24
# Version: v0.1.0a1

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_OUTPUT_DIR="$PROJECT_ROOT/test_reports/real_world_tests"
TIMESTAMP=$(date +"%Y%m%dT%H%M%SZ")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create output directory
mkdir -p "$TEST_OUTPUT_DIR"

# Change to project root
cd "$PROJECT_ROOT"

log_info "=== DevSynth Real-World Test Execution ==="
log_info "Date: $(date)"
log_info "Project Root: $PROJECT_ROOT"
log_info "Test Output: $TEST_OUTPUT_DIR"

# Validate environment
log_info "Validating DevSynth installation..."
if ! poetry run devsynth --help > /dev/null 2>&1; then
    log_error "DevSynth CLI not available or not functional"
    exit 1
fi
log_success "DevSynth CLI validated"

# Check test dependencies
log_info "Checking test dependencies..."
if ! poetry run python -c "import pytest; import tempfile; import shutil" 2>/dev/null; then
    log_error "Required test dependencies not available"
    exit 1
fi
log_success "Test dependencies validated"

# Run automated integration tests
log_info "Running automated real-world scenario tests..."
TEST_EXIT_CODE=0

# Execute tests with detailed output
poetry run pytest tests/integration/test_real_world_scenarios.py \
    -v \
    --tb=short \
    --html="$TEST_OUTPUT_DIR/real_world_tests_${TIMESTAMP}.html" \
    --self-contained-html \
    --junit-xml="$TEST_OUTPUT_DIR/real_world_tests_${TIMESTAMP}.xml" \
    2>&1 | tee "$TEST_OUTPUT_DIR/execution_log_${TIMESTAMP}.txt" || TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "All automated real-world tests passed"
else
    log_warning "Some automated tests failed (exit code: $TEST_EXIT_CODE)"
fi

# Run EDRR methodology validation
log_info "Running EDRR methodology validation..."
poetry run pytest tests/integration/test_real_world_scenarios.py::TestRealWorldScenarios::test_edrr_methodology_validation \
    -v \
    --tb=short \
    2>&1 | tee -a "$TEST_OUTPUT_DIR/execution_log_${TIMESTAMP}.txt" || {
    log_warning "EDRR methodology validation had issues"
}

# Generate summary report
log_info "Generating test execution summary..."
cat > "$TEST_OUTPUT_DIR/summary_${TIMESTAMP}.md" << EOF
# DevSynth Real-World Test Execution Summary

**Date**: $(date)
**Environment**: $(poetry env info --path)
**DevSynth Version**: $(poetry run devsynth --version 2>/dev/null || echo "Unable to determine")

## Test Results

### Automated Integration Tests
- **Exit Code**: $TEST_EXIT_CODE
- **Execution Log**: execution_log_${TIMESTAMP}.txt
- **HTML Report**: real_world_tests_${TIMESTAMP}.html
- **JUnit XML**: real_world_tests_${TIMESTAMP}.xml

### Test Cases Executed
1. **Task Manager CLI Workflow**: Validates complete CLI application development
2. **Finance Tracker API Workflow**: Validates RESTful API development with database
3. **File Organizer GUI Workflow**: Validates desktop application with GUI
4. **EDRR Methodology Validation**: Validates adherence to Expand-Differentiate-Refine-Retrospect approach

### Environment Details
- **Python Version**: $(python --version)
- **Poetry Version**: $(poetry --version)
- **Working Directory**: $PROJECT_ROOT
- **Test Timestamp**: $TIMESTAMP

### Artifacts Generated
All test artifacts are available in: $TEST_OUTPUT_DIR/

## Next Steps

$(if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ **All tests passed** - DevSynth real-world scenarios are functioning correctly"
    echo ""
    echo "**Recommendations:**"
    echo "- Proceed with v0.1.0a1 release validation"
    echo "- Execute manual test scenarios for comprehensive UX validation"
    echo "- Consider adding these tests to CI/CD pipeline"
else
    echo "⚠️  **Some tests failed** - Review execution log for details"
    echo ""
    echo "**Recommendations:**"
    echo "- Check execution_log_${TIMESTAMP}.txt for specific failure details"
    echo "- Validate DevSynth environment configuration"
    echo "- Re-run individual test cases for debugging"
fi)

## Manual Test Execution

For comprehensive validation, also execute the manual test scenarios documented in:
- tests/integration/real_world_test_plans.md
- tests/integration/real_world_execution_guide.md

These manual tests provide full user experience validation beyond the automated scenarios.
EOF

# Display summary
log_info "Test execution complete. Summary:"
cat "$TEST_OUTPUT_DIR/summary_${TIMESTAMP}.md"

# Final status
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "=== All Real-World Tests Completed Successfully ==="
    log_info "Reports available in: $TEST_OUTPUT_DIR/"
    exit 0
else
    log_warning "=== Real-World Tests Completed with Issues ==="
    log_info "Check logs in: $TEST_OUTPUT_DIR/"
    exit $TEST_EXIT_CODE
fi
