#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# If any command in a pipeline fails, that return code is used as the result of the whole pipeline.
set -o pipefail

# QuantumAlpha Setup Script
# This script installs dependencies for the backend (Python) and frontends (Node.js)

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
WEB_FRONTEND_DIR="$PROJECT_ROOT/web-frontend"
MOBILE_FRONTEND_DIR="$PROJECT_ROOT/mobile-frontend"

# --- Utility Functions ---

print_header() {
    echo -e "\n========================================"
    echo -e " $1"
    echo -e "========================================"
}

# --- Main Setup Logic ---

print_header "Starting QuantumAlpha Project Setup"

# 1. Backend Setup (Python)
print_header "1. Setting up Backend Dependencies (Python)"
if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    echo "Installing Python dependencies from requirements.txt..."
    # Assuming a virtual environment is preferred, but installing globally for simplicity in a script
    # A more robust script would check for a venv and activate it.
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    elif command -v pip &> /dev/null; then
        pip install -r requirements.txt
    else
        echo "Warning: pip or pip3 not found. Skipping Python dependency installation."
    fi
    cd "$PROJECT_ROOT"
else
    echo "Warning: Backend directory not found at $BACKEND_DIR. Skipping backend setup."
fi

# 2. Web Frontend Setup (Node.js)
print_header "2. Setting up Web Frontend Dependencies (Node.js)"
if [ -d "$WEB_FRONTEND_DIR" ]; then
    cd "$WEB_FRONTEND_DIR"
    echo "Installing Node.js dependencies for web-frontend..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v npm &> /dev/null; then
        npm install
    else
        echo "Warning: pnpm or npm not found. Skipping web frontend dependency installation."
    fi
    cd "$PROJECT_ROOT"
else
    echo "Warning: Web frontend directory not found at $WEB_FRONTEND_DIR. Skipping web frontend setup."
fi

# 3. Mobile Frontend Setup (Node.js)
print_header "3. Setting up Mobile Frontend Dependencies (Node.js)"
if [ -d "$MOBILE_FRONTEND_DIR" ]; then
    cd "$MOBILE_FRONTEND_DIR"
    echo "Installing Node.js dependencies for mobile-frontend..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v npm &> /dev/null; then
        npm install
    else
        echo "Warning: pnpm or npm not found. Skipping mobile frontend dependency installation."
    fi
    cd "$PROJECT_ROOT"
else
    echo "Warning: Mobile frontend directory not found at $MOBILE_FRONTEND_DIR. Skipping mobile frontend setup."
fi

print_header "QuantumAlpha Setup Complete!"
echo "Run './scripts/start.sh' to launch the application."
