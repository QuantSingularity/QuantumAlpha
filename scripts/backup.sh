#!/bin/bash
# QuantumAlpha Backup Script
# This script performs backups of databases and configurations for the QuantumAlpha platform

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
ENV="dev"
COMPONENTS="all"
BACKUP_DIR="$PROJECT_ROOT/backups"
S3_BUCKET=""
S3_PREFIX="quantumalpha-backups"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--env)
      ENV="$2"
      shift
      shift
      ;;
    -c|--components)
      COMPONENTS="$2"
      shift
      shift
      ;;
    -d|--backup-dir)
      BACKUP_DIR="$2"
      shift
      shift
      ;;
    -s|--s3-bucket)
      S3_BUCKET="$2"
      shift
      shift
      ;;
    -p|--s3-prefix)
      S3_PREFIX="$2"
      shift
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV          Environment (dev, staging, prod). Default: dev"
      echo "  -c, --components COMP  Components to backup (all, postgres, influxdb, config)"
      echo "                         Comma-separated list for multiple components. Default: all"
      echo "  -d, --backup-dir DIR   Local backup directory. Default: ./backups"
      echo "  -s, --s3-bucket BUCKET S3 bucket for backup storage"
      echo "  -p, --s3-prefix PREFIX S3 prefix (folder) for backups. Default: quantumalpha-backups"
      echo "  --dry-run              Print commands without executing them"
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

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
  echo -e "${RED}Error: Invalid environment '$ENV'. Must be one of: dev, staging, prod${NC}"
  exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Backup ($ENV)             ${NC}"
echo -e "${BLUE}  Timestamp: $TIMESTAMP                  ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Function to execute or print command
execute_cmd() {
  if $DRY_RUN; then
    echo -e "${YELLOW}[DRY RUN] ${BLUE}$1${NC}"
  else
    echo -e "${BLUE}Executing: $1${NC}"
    eval $1
  fi
}

# Create backup directory
BACKUP_PATH="$BACKUP_DIR/$ENV/$TIMESTAMP"
mkdir -p "$BACKUP_PATH"
echo -e "${GREEN}✓ Created backup directory: $BACKUP_PATH${NC}"

# Load environment variables
if [[ -f "$PROJECT_ROOT/config/.env.$ENV" ]]; then
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/config/.env.$ENV"
  echo -e "${GREEN}✓ Loaded environment variables from .env.$ENV${NC}"
else
  echo -e "${YELLOW}Warning: .env.$ENV file not found. Using default environment variables.${NC}"
fi

# Parse components
if [[ "$COMPONENTS" == "all" ]]; then
  COMPONENTS_ARRAY=("postgres" "influxdb" "config")
else
  IFS=',' read -ra COMPONENTS_ARRAY <<< "$COMPONENTS"
fi

# Process each component
for COMPONENT in "${COMPONENTS_ARRAY[@]}"; do
  case $COMPONENT in
    postgres)
      echo -e "\n${YELLOW}Backing up PostgreSQL database...${NC}"

      # Set default values if not in environment
      DB_HOST=${DB_HOST:-localhost}
      DB_PORT=${DB_PORT:-5432}
      DB_USERNAME=${DB_USERNAME:-postgres}
      DB_PASSWORD=${DB_PASSWORD:-postgres}
      DB_NAME=${DB_NAME:-quantumalpha}

      # Create backup directory for PostgreSQL
      mkdir -p "$BACKUP_PATH/postgres"

      # Set PGPASSWORD environment variable
      export PGPASSWORD="$DB_PASSWORD"

      # Backup schema
      SCHEMA_BACKUP_CMD="pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME --schema-only -f $BACKUP_PATH/postgres/schema.sql"
      execute_cmd "$SCHEMA_BACKUP_CMD"

      # Backup data
      DATA_BACKUP_CMD="pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME --data-only -f $BACKUP_PATH/postgres/data.sql"
      execute_cmd "$DATA_BACKUP_CMD"

      # Backup full database (compressed)
      FULL_BACKUP_CMD="pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME -Fc -f $BACKUP_PATH/postgres/full_backup.dump"
      execute_cmd "$FULL_BACKUP_CMD"

      # Clear PGPASSWORD
      unset PGPASSWORD

      echo -e "${GREEN}✓ PostgreSQL backup completed${NC}"
      ;;

    influxdb)
      echo -e "\n${YELLOW}Backing up InfluxDB...${NC}"

      # Set default values if not in environment
      INFLUXDB_URL=${INFLUXDB_URL:-http://localhost:8086}
      INFLUXDB_ORG=${INFLUXDB_ORG:-quantumalpha}
      INFLUXDB_TOKEN=${INFLUXDB_TOKEN:-}
      INFLUXDB_BUCKET=${INFLUXDB_BUCKET:-market_data}

      # Create backup directory for InfluxDB
      mkdir -p "$BACKUP_PATH/influxdb"

      # Check if influx CLI is installed
      if ! command -v influx &> /dev/null; then
        echo -e "${YELLOW}Warning: influx CLI not found. Using Docker for backup.${NC}"

        # Use Docker to backup InfluxDB
        INFLUX_BACKUP_CMD="docker run --rm \
          -v $BACKUP_PATH/influxdb:/backup \
          -e INFLUX_HOST=$INFLUXDB_URL \
          -e INFLUX_ORG=$INFLUXDB_ORG \
          -e INFLUX_TOKEN=$INFLUXDB_TOKEN \
          influxdb:2.0 \
          influx backup /backup --bucket $INFLUXDB_BUCKET"
        execute_cmd "$INFLUX_BACKUP_CMD"
      else
        # Use influx CLI directly
        INFLUX_BACKUP_CMD="influx backup $BACKUP_PATH/influxdb --host $INFLUXDB_URL --org $INFLUXDB_ORG --token $INFLUXDB_TOKEN --bucket $INFLUXDB_BUCKET"
        execute_cmd "$INFLUX_BACKUP_CMD"
      fi

      echo -e "${GREEN}✓ InfluxDB backup completed${NC}"
      ;;

    config)
      echo -e "\n${YELLOW}Backing up configuration files...${NC}"

      # Create backup directory for config
      mkdir -p "$BACKUP_PATH/config"

      # Backup config directory
      CONFIG_BACKUP_CMD="cp -r $PROJECT_ROOT/config/* $BACKUP_PATH/config/"
      execute_cmd "$CONFIG_BACKUP_CMD"

      echo -e "${GREEN}✓ Configuration backup completed${NC}"
      ;;

    *)
      echo -e "${RED}Error: Unknown component: $COMPONENT${NC}"
      echo "Available components: postgres, influxdb, config"
      ;;
  esac
done

# Compress backup
echo -e "\n${YELLOW}Compressing backup...${NC}"
COMPRESS_CMD="tar -czf $BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz -C $BACKUP_DIR/$ENV $TIMESTAMP"
execute_cmd "$COMPRESS_CMD"
echo -e "${GREEN}✓ Backup compressed: $BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz${NC}"

# Upload to S3 if bucket is specified
if [[ ! -z "$S3_BUCKET" ]]; then
  echo -e "\n${YELLOW}Uploading backup to S3...${NC}"

  # Check if AWS CLI is installed
  if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found${NC}"
  else
    S3_PATH="s3://$S3_BUCKET/$S3_PREFIX/$ENV/$TIMESTAMP.tar.gz"
    S3_UPLOAD_CMD="aws s3 cp $BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz $S3_PATH"
    execute_cmd "$S3_UPLOAD_CMD"
    echo -e "${GREEN}✓ Backup uploaded to S3: $S3_PATH${NC}"
  fi
fi

# Clean up old backups (keep last 5)
echo -e "\n${YELLOW}Cleaning up old backups...${NC}"
CLEANUP_CMD="ls -t $BACKUP_DIR/$ENV-*.tar.gz | tail -n +6 | xargs rm -f"
execute_cmd "$CLEANUP_CMD"
CLEANUP_DIR_CMD="rm -rf $BACKUP_PATH"
execute_cmd "$CLEANUP_DIR_CMD"
echo -e "${GREEN}✓ Old backups cleaned up${NC}"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Backup Completed          ${NC}"
echo -e "${GREEN}  Backup file: $BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz${NC}"
echo -e "${GREEN}=========================================${NC}"
