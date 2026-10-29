#!/bin/bash
# QuantumAlpha Development Environment Startup Script
# This script starts all services for local development

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
START_INFRASTRUCTURE=true
START_BACKEND=true
START_FRONTEND=true
START_MONITORING=false
DETACHED=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --no-infrastructure)
      START_INFRASTRUCTURE=false
      shift
      ;;
    --no-backend)
      START_BACKEND=false
      shift
      ;;
    --no-frontend)
      START_FRONTEND=false
      shift
      ;;
    --with-monitoring)
      START_MONITORING=true
      shift
      ;;
    -d|--detached)
      DETACHED=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --no-infrastructure  Don't start infrastructure services (PostgreSQL, InfluxDB, Redis, Kafka)"
      echo "  --no-backend         Don't start backend services"
      echo "  --no-frontend        Don't start frontend services"
      echo "  --with-monitoring    Start monitoring services (Prometheus, Grafana)"
      echo "  -d, --detached       Run services in detached mode"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Development Environment   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if virtual environment exists and activate it
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo -e "${RED}Error: Virtual environment not found. Please run setup_env.sh first.${NC}"
  exit 1
fi

# shellcheck source=/dev/null
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✓ Activated virtual environment${NC}"

# Check if .env file exists
if [[ ! -f "$PROJECT_ROOT/config/.env" ]]; then
  echo -e "${RED}Error: .env file not found. Please run setup_env.sh first.${NC}"
  exit 1
fi

# Load environment variables
# shellcheck source=/dev/null
source "$PROJECT_ROOT/config/.env"

# Start infrastructure services
if $START_INFRASTRUCTURE; then
  echo -e "\n${YELLOW}Starting infrastructure services...${NC}"

  DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.yml"

  if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo -e "${RED}Error: Docker Compose file not found: $DOCKER_COMPOSE_FILE${NC}"
    exit 1
  fi

  SERVICES="postgres influxdb redis kafka zookeeper"

  if $START_MONITORING; then
    SERVICES="$SERVICES prometheus grafana"
  fi

  if $DETACHED; then
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d $SERVICES
  else
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d $SERVICES
  fi

  echo -e "${GREEN}✓ Infrastructure services started${NC}"

  # Wait for services to be ready
  echo -e "${YELLOW}Waiting for services to be ready...${NC}"
  sleep 5
fi

# Start backend services
if $START_BACKEND; then
  echo -e "\n${YELLOW}Starting backend services...${NC}"

  # Create log directory if it doesn't exist
  mkdir -p "$PROJECT_ROOT/logs"

  # Start data service
  echo -e "${BLUE}Starting data service...${NC}"
  cd "$PROJECT_ROOT/backend/data_service"
  python app.py > "$PROJECT_ROOT/logs/data_service.log" 2>&1 &
  DATA_SERVICE_PID=$!
  echo $DATA_SERVICE_PID > "$PROJECT_ROOT/logs/data_service.pid"
  echo -e "${GREEN}✓ Data service started (PID: $DATA_SERVICE_PID)${NC}"

  # Wait for data service to be ready
  sleep 2

  # Start AI engine
  echo -e "${BLUE}Starting AI engine...${NC}"
  cd "$PROJECT_ROOT/backend/ai_engine"
  python app.py > "$PROJECT_ROOT/logs/ai_engine.log" 2>&1 &
  AI_ENGINE_PID=$!
  echo $AI_ENGINE_PID > "$PROJECT_ROOT/logs/ai_engine.pid"
  echo -e "${GREEN}✓ AI engine started (PID: $AI_ENGINE_PID)${NC}"

  # Wait for AI engine to be ready
  sleep 2

  # Start risk service
  echo -e "${BLUE}Starting risk service...${NC}"
  cd "$PROJECT_ROOT/backend/risk_service"
  python app.py > "$PROJECT_ROOT/logs/risk_service.log" 2>&1 &
  RISK_SERVICE_PID=$!
  echo $RISK_SERVICE_PID > "$PROJECT_ROOT/logs/risk_service.pid"
  echo -e "${GREEN}✓ Risk service started (PID: $RISK_SERVICE_PID)${NC}"

  # Wait for risk service to be ready
  sleep 2

  # Start execution service
  echo -e "${BLUE}Starting execution service...${NC}"
  cd "$PROJECT_ROOT/backend/execution_service"
  python app.py > "$PROJECT_ROOT/logs/execution_service.log" 2>&1 &
  EXECUTION_SERVICE_PID=$!
  echo $EXECUTION_SERVICE_PID > "$PROJECT_ROOT/logs/execution_service.pid"
  echo -e "${GREEN}✓ Execution service started (PID: $EXECUTION_SERVICE_PID)${NC}"

  cd "$PROJECT_ROOT"
fi

# Start frontend services
if $START_FRONTEND; then
  echo -e "\n${YELLOW}Starting frontend services...${NC}"

  # Start web frontend
  echo -e "${BLUE}Starting web frontend...${NC}"
  cd "$PROJECT_ROOT/web-frontend"
  npm start > "$PROJECT_ROOT/logs/web_frontend.log" 2>&1 &
  WEB_FRONTEND_PID=$!
  echo $WEB_FRONTEND_PID > "$PROJECT_ROOT/logs/web_frontend.pid"
  echo -e "${GREEN}✓ Web frontend started (PID: $WEB_FRONTEND_PID)${NC}"

  cd "$PROJECT_ROOT"
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Development Environment   ${NC}"
echo -e "${GREEN}  Started Successfully                   ${NC}"
echo -e "${GREEN}=========================================${NC}"

echo -e "\nServices:"
echo -e "  - Data Service:      http://localhost:8081"
echo -e "  - AI Engine:         http://localhost:8082"
echo -e "  - Risk Service:      http://localhost:8083"
echo -e "  - Execution Service: http://localhost:8084"
echo -e "  - Web Frontend:      http://localhost:3000"

if $START_MONITORING; then
  echo -e "  - Prometheus:       http://localhost:9090"
  echo -e "  - Grafana:          http://localhost:3000"
fi

echo -e "\nTo stop all services, run: ${BLUE}./scripts/stop_services.sh${NC}"
echo -e "To view logs, check the ${BLUE}./logs/${NC} directory"

# If not detached, show logs
if ! $DETACHED && $START_BACKEND; then
  echo -e "\n${YELLOW}Showing logs (Ctrl+C to stop)...${NC}"
  tail -f "$PROJECT_ROOT/logs/data_service.log" "$PROJECT_ROOT/logs/ai_engine.log" "$PROJECT_ROOT/logs/risk_service.log" "$PROJECT_ROOT/logs/execution_service.log"
fi
