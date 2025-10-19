#!/bin/bash
# Script to run tests with different strategies for better performance

# Default values
PARALLEL=4
CATEGORY="all"
MARKERS=""
VERBOSE=0
COVERAGE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--parallel)
      PARALLEL="$2"
      shift 2
      ;;
    -c|--category)
      CATEGORY="$2"
      shift 2
      ;;
    -m|--markers)
      MARKERS="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=1
      shift
      ;;
    --coverage)
      COVERAGE=1
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-p|--parallel NUM] [-c|--category CATEGORY] [-m|--markers MARKERS] [-v|--verbose] [--coverage]"
      echo "Categories: all, unit, integration, behavior, performance, property, fast, medium, slow"
      exit 1
      ;;
  esac
done

# Set verbosity flag
if [ $VERBOSE -eq 1 ]; then
  VERBOSE_FLAG="-v"
else
  VERBOSE_FLAG=""
fi

# Set coverage flag
if [ $COVERAGE -eq 1 ]; then
  COVERAGE_FLAG="--cov=src/devsynth --cov-report=term --cov-report=html"
else
  COVERAGE_FLAG=""
fi

# Function to run tests with xdist
run_parallel_tests() {
  local test_path=$1
  local markers=$2

  if [ -n "$markers" ]; then
    echo "Running tests in $test_path with markers: $markers"
    python -m pytest $test_path -m "$markers" -xvs $VERBOSE_FLAG $COVERAGE_FLAG -n $PARALLEL
  else
    echo "Running tests in $test_path"
    python -m pytest $test_path $VERBOSE_FLAG $COVERAGE_FLAG -n $PARALLEL
  fi
}

# Function to run tests that require isolation
run_isolation_tests() {
  local test_path=$1

  echo "Running isolation tests in $test_path"
  python -m pytest $test_path -m "isolation" $VERBOSE_FLAG $COVERAGE_FLAG
}

# Main execution based on category
case $CATEGORY in
  all)
    echo "Running all tests with parallelism ($PARALLEL processes)"
    # Run non-isolation tests in parallel
    run_parallel_tests "tests/" "not isolation and $MARKERS"
    # Run isolation tests sequentially
    run_isolation_tests "tests/"
    ;;

  unit)
    echo "Running unit tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/unit/" "$MARKERS"
    ;;

  integration)
    echo "Running integration tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/integration/" "$MARKERS"
    ;;

  behavior)
    echo "Running behavior tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/behavior/" "$MARKERS"
    ;;

  performance)
    echo "Running performance tests"
    # Performance tests are run sequentially to avoid interference
    python -m pytest tests/performance/ $VERBOSE_FLAG $COVERAGE_FLAG
    ;;

  property)
    echo "Running property tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/property/" "$MARKERS"
    ;;

  fast)
    echo "Running fast tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/" "fast and $MARKERS"
    ;;

  medium)
    echo "Running medium tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/" "medium and $MARKERS"
    ;;

  slow)
    echo "Running slow tests with parallelism ($PARALLEL processes)"
    run_parallel_tests "tests/" "slow and $MARKERS"
    ;;

  *)
    echo "Unknown category: $CATEGORY"
    echo "Available categories: all, unit, integration, behavior, performance, property, fast, medium, slow"
    exit 1
    ;;
esac

echo "Test execution complete"
