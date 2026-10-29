#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# If any command in a pipeline fails, that return code is used as the result of the whole pipeline.
set -o pipefail

# QuantumAlpha Start Script
# This script starts the entire application using docker-compose.

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# --- Utility Functions ---

print_header() {
    echo -e "\n========================================"
    echo -e " $1"
    echo -e "========================================"
}

# --- Main Start Logic ---

print_header "Starting QuantumAlpha Application with Docker Compose"

# Check for docker-compose file
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
    exit 1
fi

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker or Docker Compose is not installed. Please install them to run the application."
    exit 1
fi

# Build and start the services in detached mode
echo "Building and starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d

echo "Waiting for services to become healthy..."
# A more robust check would be to use 'docker-compose ps' and check health status,
# but for a general start script, a simple wait is often sufficient.
sleep 5

echo "Services started successfully!"
echo "To view logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
echo "To stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
