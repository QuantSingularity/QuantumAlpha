#!/bin/bash
# QuantumAlpha Test Runner Script
# This script runs tests for the QuantumAlpha platform

set -e

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default options
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_SYSTEM=false
COVERAGE=false
VERBOSE=false
PARALLEL=false
JUNIT_REPORT=false
TEST_PATH="$PROJECT_ROOT/tests"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --unit-only)
      RUN_UNIT=true
      RUN_INTEGRATION=false
      RUN_SYSTEM=false
      shift
      ;;
    --integration-only)
      RUN_UNIT=false
      RUN_INTEGRATION=true
      RUN_SYSTEM=false
      shift
      ;;
    --system-only)
      RUN_UNIT=false
      RUN_INTEGRATION=false
      RUN_SYSTEM=true
      shift
      ;;
    --with-system)
      RUN_SYSTEM=true
      shift
      ;;
    --coverage)
      COVERAGE=true
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -p|--parallel)
      PARALLEL=true
      shift
      ;;
    --junit)
      JUNIT_REPORT=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options] [test_path]"
      echo "Options:"
      echo "  --unit-only        Run only unit tests"
      echo "  --integration-only Run only integration tests"
      echo "  --system-only      Run only system tests"
      echo "  --with-system      Include system tests"
      echo "  --coverage         Generate coverage report"
      echo "  -v, --verbose      Verbose output"
      echo "  -p, --parallel     Run tests in parallel"
      echo "  --junit            Generate JUnit XML reports"
      echo "  -h, --help         Show this help message"
      echo ""
      echo "Arguments:"
      echo "  test_path          Path to specific test file or directory"
      exit 0
      ;;
    *)
      # If the argument doesn't start with -, assume it's a test path
      if [[ "$1" != -* ]]; then
        TEST_PATH="$1"
      else
        echo "Unknown option: $1"
        echo "Use -h or --help for usage information"
        exit 1
      fi
      shift
      ;;
  esac
done

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Test Runner               ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if virtual environment exists and activate it
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo -e "${RED}Error: Virtual environment not found. Please run setup_env.sh first.${NC}"
  exit 1
fi

# shellcheck source=/dev/null
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✓ Activated virtual environment${NC}"

# Build pytest command
PYTEST_CMD="python -m pytest"

if $VERBOSE; then
  PYTEST_CMD="$PYTEST_CMD -v"
fi

if $PARALLEL; then
  PYTEST_CMD="$PYTEST_CMD -xvs -n auto"
fi

if $JUNIT_REPORT; then
  mkdir -p "$PROJECT_ROOT/test-reports"
  PYTEST_CMD="$PYTEST_CMD --junitxml=$PROJECT_ROOT/test-reports/junit.xml"
fi

# Create test results directory
mkdir -p "$PROJECT_ROOT/test-results"

# Run unit tests
if $RUN_UNIT; then
  echo -e "\n${YELLOW}Running unit tests...${NC}"

  UNIT_CMD="$PYTEST_CMD"

  if [[ "$TEST_PATH" == "$PROJECT_ROOT/tests" ]]; then
    # If no specific test path is provided, run all unit tests
    UNIT_CMD="$UNIT_CMD $PROJECT_ROOT/tests/unit"
  else
    # If a specific test path is provided, use it
    UNIT_CMD="$UNIT_CMD $TEST_PATH"
  fi

  if $COVERAGE; then
    UNIT_CMD="$UNIT_CMD --cov=backend --cov-report=term --cov-report=html:$PROJECT_ROOT/test-results/coverage"
  fi

  echo -e "${BLUE}Command: $UNIT_CMD${NC}"
  eval $UNIT_CMD

  echo -e "${GREEN}✓ Unit tests completed${NC}"
fi

# Run integration tests
if $RUN_INTEGRATION; then
  echo -e "\n${YELLOW}Running integration tests...${NC}"

  INTEGRATION_CMD="$PYTEST_CMD"

  if [[ "$TEST_PATH" == "$PROJECT_ROOT/tests" ]]; then
    # If no specific test path is provided, run all integration tests
    INTEGRATION_CMD="$INTEGRATION_CMD $PROJECT_ROOT/tests/integration"
  else
    # If a specific test path is provided, use it
    INTEGRATION_CMD="$INTEGRATION_CMD $TEST_PATH"
  fi

  if $COVERAGE && ! $RUN_UNIT; then
    # Only add coverage if unit tests weren't run (to avoid duplicate coverage)
    INTEGRATION_CMD="$INTEGRATION_CMD --cov=backend --cov-report=term --cov-report=html:$PROJECT_ROOT/test-results/coverage"
  fi

  echo -e "${BLUE}Command: $INTEGRATION_CMD${NC}"
  eval $INTEGRATION_CMD

  echo -e "${GREEN}✓ Integration tests completed${NC}"
fi

# Run system tests
if $RUN_SYSTEM; then
  echo -e "\n${YELLOW}Running system tests...${NC}"

  SYSTEM_CMD="$PYTEST_CMD"

  if [[ "$TEST_PATH" == "$PROJECT_ROOT/tests" ]]; then
    # If no specific test path is provided, run all system tests
    SYSTEM_CMD="$SYSTEM_CMD $PROJECT_ROOT/tests/system"
  else
    # If a specific test path is provided, use it
    SYSTEM_CMD="$SYSTEM_CMD $TEST_PATH"
  fi

  if $COVERAGE && ! $RUN_UNIT && ! $RUN_INTEGRATION; then
    # Only add coverage if other tests weren't run (to avoid duplicate coverage)
    SYSTEM_CMD="$SYSTEM_CMD --cov=backend --cov-report=term --cov-report=html:$PROJECT_ROOT/test-results/coverage"
  fi

  echo -e "${BLUE}Command: $SYSTEM_CMD${NC}"
  eval $SYSTEM_CMD

  echo -e "${GREEN}✓ System tests completed${NC}"
fi

# Show coverage report location if generated
if $COVERAGE; then
  echo -e "\n${YELLOW}Coverage report generated at:${NC}"
  echo -e "${BLUE}$PROJECT_ROOT/test-results/coverage/index.html${NC}"
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Tests Completed           ${NC}"
echo -e "${GREEN}=========================================${NC}"
