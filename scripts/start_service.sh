#!/bin/bash
# QuantumAlpha Service Starter Script
# This script starts individual services for the QuantumAlpha platform

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
SERVICE=""
ENV="dev"
DEBUG=false
PORT=""
DETACHED=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -s|--service)
      SERVICE="$2"
      shift
      shift
      ;;
    -e|--env)
      ENV="$2"
      shift
      shift
      ;;
    -d|--debug)
      DEBUG=true
      shift
      ;;
    -p|--port)
      PORT="$2"
      shift
      shift
      ;;
    --detached)
      DETACHED=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -s, --service SERVICE  Service to start (data-service, ai-engine, risk-service, execution-service, web-frontend)"
      echo "  -e, --env ENV          Environment (dev, staging, prod). Default: dev"
      echo "  -d, --debug            Start service in debug mode"
      echo "  -p, --port PORT        Override default port"
      echo "  --detached             Run service in detached mode"
      echo "  -h, --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Validate service
if [[ -z "$SERVICE" ]]; then
  echo -e "${RED}Error: Service not specified${NC}"
  echo "Use -s or --service to specify a service"
  echo "Available services: data-service, ai-engine, risk-service, execution-service, web-frontend"
  exit 1
fi

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
  echo -e "${RED}Error: Invalid environment '$ENV'. Must be one of: dev, staging, prod${NC}"
  exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Service Starter            ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if virtual environment exists and activate it
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo -e "${RED}Error: Virtual environment not found. Please run setup_env.sh first.${NC}"
  exit 1
fi

# shellcheck source=/dev/null
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✓ Activated virtual environment${NC}"

# Load environment variables
if [[ -f "$PROJECT_ROOT/config/.env.$ENV" ]]; then
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/config/.env.$ENV"
  echo -e "${GREEN}✓ Loaded environment variables from .env.$ENV${NC}"
else
  echo -e "${YELLOW}Warning: .env.$ENV file not found. Using default environment variables.${NC}"
fi

# Create log directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start the specified service
case $SERVICE in
  data-service)
    echo -e "\n${YELLOW}Starting data service...${NC}"

    SERVICE_DIR="$PROJECT_ROOT/backend/data_service"
    LOG_FILE="$PROJECT_ROOT/logs/data_service.log"
    PID_FILE="$PROJECT_ROOT/logs/data_service.pid"

    if [[ ! -d "$SERVICE_DIR" ]]; then
      echo -e "${RED}Error: Data service directory not found: $SERVICE_DIR${NC}"
      exit 1
    fi

    cd "$SERVICE_DIR"

    # Set port if specified
    if [[ ! -z "$PORT" ]]; then
      export APP_PORT="$PORT"
      echo -e "${BLUE}Using custom port: $PORT${NC}"
    fi

    # Start service
    if $DEBUG; then
      echo -e "${BLUE}Starting data service in debug mode...${NC}"
      if $DETACHED; then
        python app.py --debug > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Data service started in debug mode (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py --debug
      fi
    else
      if $DETACHED; then
        python app.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Data service started (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py
      fi
    fi
    ;;

  ai-engine)
    echo -e "\n${YELLOW}Starting AI engine...${NC}"

    SERVICE_DIR="$PROJECT_ROOT/backend/ai_engine"
    LOG_FILE="$PROJECT_ROOT/logs/ai_engine.log"
    PID_FILE="$PROJECT_ROOT/logs/ai_engine.pid"

    if [[ ! -d "$SERVICE_DIR" ]]; then
      echo -e "${RED}Error: AI engine directory not found: $SERVICE_DIR${NC}"
      exit 1
    fi

    cd "$SERVICE_DIR"

    # Set port if specified
    if [[ ! -z "$PORT" ]]; then
      export APP_PORT="$PORT"
      echo -e "${BLUE}Using custom port: $PORT${NC}"
    fi

    # Start service
    if $DEBUG; then
      echo -e "${BLUE}Starting AI engine in debug mode...${NC}"
      if $DETACHED; then
        python app.py --debug > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ AI engine started in debug mode (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py --debug
      fi
    else
      if $DETACHED; then
        python app.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ AI engine started (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py
      fi
    fi
    ;;

  risk-service)
    echo -e "\n${YELLOW}Starting risk service...${NC}"

    SERVICE_DIR="$PROJECT_ROOT/backend/risk_service"
    LOG_FILE="$PROJECT_ROOT/logs/risk_service.log"
    PID_FILE="$PROJECT_ROOT/logs/risk_service.pid"

    if [[ ! -d "$SERVICE_DIR" ]]; then
      echo -e "${RED}Error: Risk service directory not found: $SERVICE_DIR${NC}"
      exit 1
    fi

    cd "$SERVICE_DIR"

    # Set port if specified
    if [[ ! -z "$PORT" ]]; then
      export APP_PORT="$PORT"
      echo -e "${BLUE}Using custom port: $PORT${NC}"
    fi

    # Start service
    if $DEBUG; then
      echo -e "${BLUE}Starting risk service in debug mode...${NC}"
      if $DETACHED; then
        python app.py --debug > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Risk service started in debug mode (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py --debug
      fi
    else
      if $DETACHED; then
        python app.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Risk service started (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py
      fi
    fi
    ;;

  execution-service)
    echo -e "\n${YELLOW}Starting execution service...${NC}"

    SERVICE_DIR="$PROJECT_ROOT/backend/execution_service"
    LOG_FILE="$PROJECT_ROOT/logs/execution_service.log"
    PID_FILE="$PROJECT_ROOT/logs/execution_service.pid"

    if [[ ! -d "$SERVICE_DIR" ]]; then
      echo -e "${RED}Error: Execution service directory not found: $SERVICE_DIR${NC}"
      exit 1
    fi

    cd "$SERVICE_DIR"

    # Set port if specified
    if [[ ! -z "$PORT" ]]; then
      export APP_PORT="$PORT"
      echo -e "${BLUE}Using custom port: $PORT${NC}"
    fi

    # Start service
    if $DEBUG; then
      echo -e "${BLUE}Starting execution service in debug mode...${NC}"
      if $DETACHED; then
        python app.py --debug > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Execution service started in debug mode (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py --debug
      fi
    else
      if $DETACHED; then
        python app.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Execution service started (PID: $(cat $PID_FILE))${NC}"
      else
        python app.py
      fi
    fi
    ;;

  web-frontend)
    echo -e "\n${YELLOW}Starting web frontend...${NC}"

    SERVICE_DIR="$PROJECT_ROOT/web-frontend"
    LOG_FILE="$PROJECT_ROOT/logs/web_frontend.log"
    PID_FILE="$PROJECT_ROOT/logs/web_frontend.pid"

    if [[ ! -d "$SERVICE_DIR" ]]; then
      echo -e "${RED}Error: Web frontend directory not found: $SERVICE_DIR${NC}"
      exit 1
    fi

    cd "$SERVICE_DIR"

    # Set port if specified
    if [[ ! -z "$PORT" ]]; then
      export PORT="$PORT"
      echo -e "${BLUE}Using custom port: $PORT${NC}"
    fi

    # Start service
    if $DEBUG; then
      echo -e "${BLUE}Starting web frontend in debug mode...${NC}"
      if $DETACHED; then
        BROWSER=none npm start > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Web frontend started in debug mode (PID: $(cat $PID_FILE))${NC}"
      else
        BROWSER=none npm start
      fi
    else
      if $DETACHED; then
        BROWSER=none npm start > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo -e "${GREEN}✓ Web frontend started (PID: $(cat $PID_FILE))${NC}"
      else
        BROWSER=none npm start
      fi
    fi
    ;;

  *)
    echo -e "${RED}Error: Unknown service: $SERVICE${NC}"
    echo "Available services: data-service, ai-engine, risk-service, execution-service, web-frontend"
    exit 1
    ;;
esac

cd "$PROJECT_ROOT"

# If detached, show how to view logs
if $DETACHED; then
  echo -e "\n${YELLOW}Service started in detached mode${NC}"
  echo -e "To view logs: ${BLUE}tail -f $LOG_FILE${NC}"
  echo -e "To stop the service: ${BLUE}kill $(cat $PID_FILE)${NC}"
fi
