#!/bin/bash
# QuantumAlpha Environment Setup Script
# This script sets up the development environment for the QuantumAlpha platform

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

# Default environment
ENV="dev"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--env)
      ENV="$2"
      shift
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV    Set environment (dev, staging, prod). Default: dev"
      echo "  -h, --help       Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
  echo -e "${RED}Error: Invalid environment '$ENV'. Must be one of: dev, staging, prod${NC}"
  exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Environment Setup ($ENV)  ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check system requirements
echo -e "\n${YELLOW}Checking system requirements...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 || ("$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 8) ]]; then
  echo -e "${RED}Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
  echo -e "${RED}Error: Docker is not installed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
  echo -e "${RED}Error: Docker Compose is not installed${NC}"
  exit 1
fi
DOCKER_COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | tr -d ',')
echo -e "${GREEN}✓ Docker Compose version: $DOCKER_COMPOSE_VERSION${NC}"

# Check Node.js for frontend development
if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version | cut -c 2-)
  echo -e "${GREEN}✓ Node.js version: $NODE_VERSION${NC}"
else
  echo -e "${YELLOW}Warning: Node.js is not installed. Frontend development will not be available.${NC}"
fi

# Create virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  python3 -m venv "$PROJECT_ROOT/venv"
  echo -e "${GREEN}✓ Created virtual environment${NC}"
else
  echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✓ Activated virtual environment${NC}"

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/backend/requirements.txt"
echo -e "${GREEN}✓ Installed Python dependencies${NC}"

# Set up configuration
echo -e "\n${YELLOW}Setting up configuration...${NC}"
if [[ ! -f "$PROJECT_ROOT/config/.env" ]]; then
  echo -e "${BLUE}Creating .env file from .env.$ENV...${NC}"
  cp "$PROJECT_ROOT/config/.env.$ENV" "$PROJECT_ROOT/config/.env"
  echo -e "${GREEN}✓ Created .env file${NC}"
  echo -e "${YELLOW}Please update the .env file with your API keys and credentials.${NC}"
else
  echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Set up database
echo -e "\n${YELLOW}Setting up database...${NC}"
if command -v docker &> /dev/null; then
  echo -e "${BLUE}Starting PostgreSQL and InfluxDB containers...${NC}"
  docker-compose -f "$PROJECT_ROOT/infrastructure/docker-compose.yml" up -d postgres influxdb redis

  # Wait for PostgreSQL to be ready
  echo -e "${BLUE}Waiting for PostgreSQL to be ready...${NC}"
  sleep 5

  # Create database schema
  echo -e "${BLUE}Creating database schema...${NC}"
  python "$PROJECT_ROOT/scripts/setup_db.py" --env "$ENV"
  echo -e "${GREEN}✓ Database schema created${NC}"
else
  echo -e "${RED}Error: Docker not found. Please install Docker and Docker Compose to continue.${NC}"
  exit 1
fi

# Install frontend dependencies
echo -e "\n${YELLOW}Setting up frontend dependencies...${NC}"
if command -v npm &> /dev/null; then
  echo -e "${BLUE}Installing web frontend dependencies...${NC}"
  cd "$PROJECT_ROOT/web-frontend"
  npm install
  cd "$PROJECT_ROOT"

  if [[ -d "$PROJECT_ROOT/mobile-frontend" ]]; then
    echo -e "${BLUE}Installing mobile frontend dependencies...${NC}"
    cd "$PROJECT_ROOT/mobile-frontend"
    npm install
    cd "$PROJECT_ROOT"
  fi

  echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
  echo -e "${YELLOW}Warning: npm not found. Skipping frontend dependencies installation.${NC}"
fi

# Create log directories
echo -e "\n${YELLOW}Creating log directories...${NC}"
mkdir -p /var/log/quantumalpha
chmod 755 /var/log/quantumalpha
echo -e "${GREEN}✓ Log directories created${NC}"

# Create data directories
echo -e "\n${YELLOW}Creating data directories...${NC}"
mkdir -p "$PROJECT_ROOT/data/models"
mkdir -p "$PROJECT_ROOT/data/features"
echo -e "${GREEN}✓ Data directories created${NC}"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Environment Setup Complete  ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nTo start the development server, run: ${BLUE}./scripts/start_dev.sh${NC}"
echo -e "To run tests, run: ${BLUE}./scripts/run_tests.sh${NC}"
echo -e "To access the web dashboard, open: ${BLUE}http://localhost:3000${NC}"
