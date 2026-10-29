#!/bin/bash
# QuantumAlpha Services Stop Script
# This script stops all running services for the QuantumAlpha platform

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
STOP_INFRASTRUCTURE=true
STOP_BACKEND=true
STOP_FRONTEND=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --no-infrastructure)
      STOP_INFRASTRUCTURE=false
      shift
      ;;
    --no-backend)
      STOP_BACKEND=false
      shift
      ;;
    --no-frontend)
      STOP_FRONTEND=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --no-infrastructure  Don't stop infrastructure services (PostgreSQL, InfluxDB, Redis, Kafka)"
      echo "  --no-backend         Don't stop backend services"
      echo "  --no-frontend        Don't stop frontend services"
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
echo -e "${BLUE}  QuantumAlpha Services Stop             ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Stop backend services
if $STOP_BACKEND; then
  echo -e "\n${YELLOW}Stopping backend services...${NC}"

  # Stop data service
  if [[ -f "$PROJECT_ROOT/logs/data_service.pid" ]]; then
    DATA_SERVICE_PID=$(cat "$PROJECT_ROOT/logs/data_service.pid")
    if ps -p $DATA_SERVICE_PID > /dev/null; then
      echo -e "${BLUE}Stopping data service (PID: $DATA_SERVICE_PID)...${NC}"
      kill $DATA_SERVICE_PID 2>/dev/null || true
      echo -e "${GREEN}✓ Data service stopped${NC}"
    else
      echo -e "${YELLOW}Data service not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/data_service.pid"
  fi

  # Stop AI engine
  if [[ -f "$PROJECT_ROOT/logs/ai_engine.pid" ]]; then
    AI_ENGINE_PID=$(cat "$PROJECT_ROOT/logs/ai_engine.pid")
    if ps -p $AI_ENGINE_PID > /dev/null; then
      echo -e "${BLUE}Stopping AI engine (PID: $AI_ENGINE_PID)...${NC}"
      kill $AI_ENGINE_PID 2>/dev/null || true
      echo -e "${GREEN}✓ AI engine stopped${NC}"
    else
      echo -e "${YELLOW}AI engine not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/ai_engine.pid"
  fi

  # Stop risk service
  if [[ -f "$PROJECT_ROOT/logs/risk_service.pid" ]]; then
    RISK_SERVICE_PID=$(cat "$PROJECT_ROOT/logs/risk_service.pid")
    if ps -p $RISK_SERVICE_PID > /dev/null; then
      echo -e "${BLUE}Stopping risk service (PID: $RISK_SERVICE_PID)...${NC}"
      kill $RISK_SERVICE_PID 2>/dev/null || true
      echo -e "${GREEN}✓ Risk service stopped${NC}"
    else
      echo -e "${YELLOW}Risk service not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/risk_service.pid"
  fi

  # Stop execution service
  if [[ -f "$PROJECT_ROOT/logs/execution_service.pid" ]]; then
    EXECUTION_SERVICE_PID=$(cat "$PROJECT_ROOT/logs/execution_service.pid")
    if ps -p $EXECUTION_SERVICE_PID > /dev/null; then
      echo -e "${BLUE}Stopping execution service (PID: $EXECUTION_SERVICE_PID)...${NC}"
      kill $EXECUTION_SERVICE_PID 2>/dev/null || true
      echo -e "${GREEN}✓ Execution service stopped${NC}"
    else
      echo -e "${YELLOW}Execution service not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/execution_service.pid"
  fi
fi

# Stop frontend services
if $STOP_FRONTEND; then
  echo -e "\n${YELLOW}Stopping frontend services...${NC}"

  # Stop web frontend
  if [[ -f "$PROJECT_ROOT/logs/web_frontend.pid" ]]; then
    WEB_FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/web_frontend.pid")
    if ps -p $WEB_FRONTEND_PID > /dev/null; then
      echo -e "${BLUE}Stopping web frontend (PID: $WEB_FRONTEND_PID)...${NC}"
      kill $WEB_FRONTEND_PID 2>/dev/null || true
      echo -e "${GREEN}✓ Web frontend stopped${NC}"
    else
      echo -e "${YELLOW}Web frontend not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/web_frontend.pid"
  fi

  # Kill any remaining npm processes
  FRONTEND_PIDS=$(ps aux | grep "node.*react-scripts" | grep -v grep | awk '{print $2}')
  if [[ ! -z "$FRONTEND_PIDS" ]]; then
    echo -e "${BLUE}Stopping remaining frontend processes...${NC}"
    for PID in $FRONTEND_PIDS; do
      kill $PID 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Remaining frontend processes stopped${NC}"
  fi
fi

# Stop infrastructure services
if $STOP_INFRASTRUCTURE; then
  echo -e "\n${YELLOW}Stopping infrastructure services...${NC}"

  DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.yml"

  if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo -e "${RED}Error: Docker Compose file not found: $DOCKER_COMPOSE_FILE${NC}"
  else
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    echo -e "${GREEN}✓ Infrastructure services stopped${NC}"
  fi
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Services Stopped          ${NC}"
echo -e "${GREEN}=========================================${NC}"
