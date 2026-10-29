#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# If any command in a pipeline fails, that return code is used as the result of the whole pipeline.
set -o pipefail

# QuantumAlpha Comprehensive Lint Script
# This script runs linting tools for Python backend, React web frontend, and React Native mobile frontend

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
WEB_FRONTEND_DIR="$PROJECT_ROOT/web-frontend"
MOBILE_FRONTEND_DIR="$PROJECT_ROOT/mobile-frontend"

# Configuration directories
BACKEND_CONFIG_DIR="$BACKEND_DIR/lint_configs"
WEB_FRONTEND_CONFIG_DIR="$WEB_FRONTEND_DIR/lint_configs"
MOBILE_FRONTEND_CONFIG_DIR="$MOBILE_FRONTEND_DIR/lint_configs"

# Default flags
RUN_BACKEND=true
RUN_WEB_FRONTEND=true
RUN_MOBILE_FRONTEND=true
FIX_ISSUES=false
VERBOSE=false
REPORT=false
REPORT_DIR="$PROJECT_ROOT/lint_reports"

# Function to print usage information
print_usage() {
    echo -e "${BLUE}QuantumAlpha Comprehensive Lint Script${NC}"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -b, --backend              Run only backend linting"
    echo "  -w, --web                  Run only web frontend linting"
    echo "  -m, --mobile               Run only mobile frontend linting"
    echo "  -f, --fix                  Attempt to fix issues automatically"
    echo "  -v, --verbose              Show detailed output"
    echo "  -r, --report               Generate HTML reports"
    echo ""
    echo "Examples:"
    echo "  $0                         Run all linters"
    echo "  $0 -b -f                   Run backend linters with auto-fix"
    echo "  $0 -w -m -r                Run web and mobile linters with reports"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -b|--backend)
            RUN_BACKEND=true
            RUN_WEB_FRONTEND=false
            RUN_MOBILE_FRONTEND=false
            shift
            ;;
        -w|--web)
            RUN_BACKEND=false
            RUN_WEB_FRONTEND=true
            RUN_MOBILE_FRONTEND=false
            shift
            ;;
        -m|--mobile)
            RUN_BACKEND=false
            RUN_WEB_FRONTEND=false
            RUN_MOBILE_FRONTEND=true
            shift
            ;;
        -f|--fix)
            FIX_ISSUES=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Create reports directory if needed
if [ "$REPORT" = true ]; then
    mkdir -p "$REPORT_DIR"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print section header
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# Function to print status
print_status() {
    if [ "$2" -eq 0 ]; then
        echo -e "${GREEN}✓ $1 passed${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
    fi
}

# Function to run Python linters
run_python_linters() {
    print_header "Running Python Linters"

    local exit_code=0
    local flake8_exit=0
    local pylint_exit=0
    local black_exit=0
    local isort_exit=0

    # Check if Python tools are installed
    if ! command_exists python3; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        return 1
    fi

    # Install required Python packages if not already installed
    echo -e "${YELLOW}Checking Python linting dependencies...${NC}"
    # Check if dependencies are installed in a virtual environment or globally
    if ! python3 -m pip show flake8 > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing Python linting dependencies...${NC}"
        python3 -m pip install --quiet flake8 pylint black isort
    fi

    # Run flake8
    echo -e "${YELLOW}Running flake8...${NC}"
    if [ "$VERBOSE" = true ]; then
        python3 -m flake8 "$BACKEND_DIR" --config="$BACKEND_CONFIG_DIR/.flake8"
    else
        python3 -m flake8 "$BACKEND_DIR" --config="$BACKEND_CONFIG_DIR/.flake8" > /dev/null
    fi
    flake8_exit=$?
    print_status "flake8" $flake8_exit

    # Run pylint
    echo -e "${YELLOW}Running pylint...${NC}"
    if [ "$VERBOSE" = true ]; then
        python3 -m pylint --rcfile="$BACKEND_CONFIG_DIR/.pylintrc" "$BACKEND_DIR"
    else
        python3 -m pylint --rcfile="$BACKEND_CONFIG_DIR/.pylintrc" "$BACKEND_DIR" > /dev/null
    fi
    pylint_exit=$?
    # Pylint returns bit-coded exit codes, 0 means no error
    if [ $pylint_exit -eq 0 ] || [ $pylint_exit -eq 4 ] || [ $pylint_exit -eq 8 ] || [ $pylint_exit -eq 16 ]; then
        print_status "pylint" 0
    else
        print_status "pylint" 1
        exit_code=1
    fi

    # Run black (check mode unless fix is enabled)
    echo -e "${YELLOW}Running black...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            python3 -m black --config="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        else
            python3 -m black --quiet --config="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            python3 -m black --check --config="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        else
            python3 -m black --quiet --check --config="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        fi
    fi
    black_exit=$?
    print_status "black" $black_exit

    # Run isort (check mode unless fix is enabled)
    echo -e "${YELLOW}Running isort...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            python3 -m isort --settings-path="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        else
            python3 -m isort --quiet --settings-path="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            python3 -m isort --check-only --settings-path="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        else
            python3 -m isort --quiet --check-only --settings-path="$BACKEND_CONFIG_DIR/pyproject.toml" "$BACKEND_DIR"
        fi
    fi
    isort_exit=$?
    print_status "isort" $isort_exit

    # Generate report if requested
    if [ "$REPORT" = true ]; then
        echo -e "${YELLOW}Generating Python lint report...${NC}"
        mkdir -p "$REPORT_DIR/python"
        python3 -m flake8 "$BACKEND_DIR" --config="$BACKEND_CONFIG_DIR/.flake8" --format=html --htmldir="$REPORT_DIR/python/flake8" || true
        python3 -m pylint --rcfile="$BACKEND_CONFIG_DIR/.pylintrc" "$BACKEND_DIR" --output-format=html > "$REPORT_DIR/python/pylint_report.html" || true
    fi

    # Set exit code if any tool failed
    if [ $flake8_exit -ne 0 ] || [ $black_exit -ne 0 ] || [ $isort_exit -ne 0 ]; then
        exit_code=1
    fi

    return $exit_code
}

# Function to run JavaScript/React linters for web frontend
run_web_frontend_linters() {
    print_header "Running Web Frontend Linters"

    local exit_code=0
    local eslint_exit=0
    local prettier_exit=0

    # Check if Node.js tools are installed
    if ! command_exists npm; then
        echo -e "${RED}Error: npm is not installed${NC}"
        return 1
    fi

    # Change to web frontend directory
    cd "$WEB_FRONTEND_DIR" || return 1

    # Install required npm packages if not already installed
    echo -e "${YELLOW}Checking web frontend linting dependencies...${NC}"
    # Check if node_modules exists and install if not
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing web frontend linting dependencies...${NC}"
        # Using pnpm for faster and more reliable dependency management
        npm install --no-save eslint prettier eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y eslint-plugin-import eslint-config-prettier eslint-plugin-prettier @typescript-eslint/eslint-plugin @typescript-eslint/parser
    fi

    # Copy config files to the project directory if they don't exist
    cp -n "$WEB_FRONTEND_CONFIG_DIR/.eslintrc.js" ./ 2>/dev/null || true
    cp -n "$WEB_FRONTEND_CONFIG_DIR/.prettierrc" ./ 2>/dev/null || true
    cp -n "$WEB_FRONTEND_CONFIG_DIR/tsconfig.json" ./ 2>/dev/null || true

    # Run ESLint
    echo -e "${YELLOW}Running ESLint for web frontend...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            npx eslint --fix .
        else
            npx eslint --fix . --quiet
        fi
    else
        if [ "$VERBOSE" = true ]; then
            npx eslint .
        else
            npx eslint . --quiet
        fi
    fi
    eslint_exit=$?
    print_status "ESLint (web)" $eslint_exit

    # Run Prettier
    echo -e "${YELLOW}Running Prettier for web frontend...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            npx prettier --write .
        else
            npx prettier --write . --loglevel error
        fi
    else
        if [ "$VERBOSE" = true ]; then
            npx prettier --check .
        else
            npx prettier --check . --loglevel error
        fi
    fi
    prettier_exit=$?
    print_status "Prettier (web)" $prettier_exit

    # Generate report if requested
    if [ "$REPORT" = true ]; then
        echo -e "${YELLOW}Generating web frontend lint report...${NC}"
        mkdir -p "$REPORT_DIR/web"
        npx eslint . -f html -o "$REPORT_DIR/web/eslint_report.html" || true
    fi

    # Set exit code if any tool failed
    if [ $eslint_exit -ne 0 ] || [ $prettier_exit -ne 0 ]; then
        exit_code=1
    fi

    # Return to project root
    cd "$PROJECT_ROOT" || return 1

    return $exit_code
}

# Function to run JavaScript/React linters for mobile frontend
run_mobile_frontend_linters() {
    print_header "Running Mobile Frontend Linters"

    local exit_code=0
    local eslint_exit=0
    local prettier_exit=0

    # Check if Node.js tools are installed
    if ! command_exists npm; then
        echo -e "${RED}Error: npm is not installed${NC}"
        return 1
    fi

    # Change to mobile frontend directory
    cd "$MOBILE_FRONTEND_DIR" || return 1

    # Install required npm packages if not already installed
    echo -e "${YELLOW}Checking mobile frontend linting dependencies...${NC}"
    # Check if node_modules exists and install if not
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing mobile frontend linting dependencies...${NC}"
        # Using pnpm for faster and more reliable dependency management
        npm install --no-save eslint prettier @react-native/eslint-config eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-react-native @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-config-prettier eslint-plugin-prettier
    fi

    # Copy config files to the project directory if they don't exist
    cp -n "$MOBILE_FRONTEND_CONFIG_DIR/.eslintrc.js" ./ 2>/dev/null || true
    cp -n "$MOBILE_FRONTEND_CONFIG_DIR/.prettierrc" ./ 2>/dev/null || true
    cp -n "$MOBILE_FRONTEND_CONFIG_DIR/tsconfig.json" ./ 2>/dev/null || true

    # Run ESLint
    echo -e "${YELLOW}Running ESLint for mobile frontend...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            npx eslint --fix .
        else
            npx eslint --fix . --quiet
        fi
    else
        if [ "$VERBOSE" = true ]; then
            npx eslint .
        else
            npx eslint . --quiet
        fi
    fi
    eslint_exit=$?
    print_status "ESLint (mobile)" $eslint_exit

    # Run Prettier
    echo -e "${YELLOW}Running Prettier for mobile frontend...${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        if [ "$VERBOSE" = true ]; then
            npx prettier --write .
        else
            npx prettier --write . --loglevel error
        fi
    else
        if [ "$VERBOSE" = true ]; then
            npx prettier --check .
        else
            npx prettier --check . --loglevel error
        fi
    fi
    prettier_exit=$?
    print_status "Prettier (mobile)" $prettier_exit

    # Generate report if requested
    if [ "$REPORT" = true ]; then
        echo -e "${YELLOW}Generating mobile frontend lint report...${NC}"
        mkdir -p "$REPORT_DIR/mobile"
        npx eslint . -f html -o "$REPORT_DIR/mobile/eslint_report.html" || true
    fi

    # Set exit code if any tool failed
    if [ $eslint_exit -ne 0 ] || [ $prettier_exit -ne 0 ]; then
        exit_code=1
    fi

    # Return to project root
    cd "$PROJECT_ROOT" || return 1

    return $exit_code
}

# Main execution
echo -e "${BLUE}QuantumAlpha Comprehensive Lint Script${NC}"
echo -e "${YELLOW}Running with options:${NC}"
echo -e "  Backend: $([ "$RUN_BACKEND" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"
echo -e "  Web Frontend: $([ "$RUN_WEB_FRONTEND" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"
echo -e "  Mobile Frontend: $([ "$RUN_MOBILE_FRONTEND" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"
echo -e "  Auto-fix: $([ "$FIX_ISSUES" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"
echo -e "  Verbose: $([ "$VERBOSE" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"
echo -e "  Generate Reports: $([ "$REPORT" = true ] && echo "${GREEN}Yes${NC}" || echo "${RED}No${NC}")"

# Track overall exit code
OVERALL_EXIT=0

# Run linters based on flags
if [ "$RUN_BACKEND" = true ]; then
    run_python_linters
    if [ $? -ne 0 ]; then
        OVERALL_EXIT=1
    fi
fi

if [ "$RUN_WEB_FRONTEND" = true ]; then
    run_web_frontend_linters
    if [ $? -ne 0 ]; then
        OVERALL_EXIT=1
    fi
fi

if [ "$RUN_MOBILE_FRONTEND" = true ]; then
    run_mobile_frontend_linters
    if [ $? -ne 0 ]; then
        OVERALL_EXIT=1
    fi
fi

# Print summary
print_header "Lint Summary"
if [ $OVERALL_EXIT -eq 0 ]; then
    echo -e "${GREEN}All linters passed successfully!${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        echo -e "${GREEN}Auto-fixes were applied where possible.${NC}"
    fi
else
    echo -e "${RED}Some linters reported issues.${NC}"
    if [ "$FIX_ISSUES" = true ]; then
        echo -e "${YELLOW}Auto-fixes were applied where possible, but some issues may require manual fixes.${NC}"
    else
        echo -e "${YELLOW}Run with --fix to attempt automatic fixes.${NC}"
    fi
fi

if [ "$REPORT" = true ]; then
    echo -e "${BLUE}Lint reports generated in: $REPORT_DIR${NC}"
fi

exit $OVERALL_EXIT
