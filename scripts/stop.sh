#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# If any command in a pipeline fails, that return code is used as the result of the whole pipeline.
set -o pipefail

# QuantumAlpha Stop Script
# This script stops and removes the application containers using docker-compose.

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# --- Utility Functions ---

print_header() {
    echo -e "\n========================================"
    echo -e " $1"
    echo -e "========================================"
}

# --- Main Stop Logic ---

print_header "Stopping QuantumAlpha Application"

# Check for docker-compose file
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Cannot stop the application."
    exit 1
fi

# Stop and remove the services
echo "Stopping and removing services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down

echo "QuantumAlpha Application Stopped."
