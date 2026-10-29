#!/bin/bash
# QuantumAlpha Restore Script
# This script restores databases and configurations from backups for the QuantumAlpha platform

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
BACKUP_FILE=""
BACKUP_DIR="$PROJECT_ROOT/backups"
S3_BUCKET=""
S3_PREFIX="quantumalpha-backups"
TIMESTAMP=""
DRY_RUN=false
FORCE=false

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
    -f|--backup-file)
      BACKUP_FILE="$2"
      shift
      shift
      ;;
    -t|--timestamp)
      TIMESTAMP="$2"
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
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -e, --env ENV          Environment (dev, staging, prod). Default: dev"
      echo "  -c, --components COMP  Components to restore (all, postgres, influxdb, config)"
      echo "                         Comma-separated list for multiple components. Default: all"
      echo "  -f, --backup-file FILE Path to backup file (.tar.gz)"
      echo "  -t, --timestamp TS     Timestamp of backup to restore (format: YYYYMMDD-HHMMSS)"
      echo "                         Required if --backup-file is not specified"
      echo "  -d, --backup-dir DIR   Local backup directory. Default: ./backups"
      echo "  -s, --s3-bucket BUCKET S3 bucket for backup storage"
      echo "  -p, --s3-prefix PREFIX S3 prefix (folder) for backups. Default: quantumalpha-backups"
      echo "  --dry-run              Print commands without executing them"
      echo "  --force                Force restore without confirmation"
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

# Check if backup file or timestamp is provided
if [[ -z "$BACKUP_FILE" && -z "$TIMESTAMP" ]]; then
  echo -e "${RED}Error: Either --backup-file or --timestamp must be specified${NC}"
  exit 1
fi

# If timestamp is provided but not backup file, construct backup file path
if [[ -z "$BACKUP_FILE" && ! -z "$TIMESTAMP" ]]; then
  if [[ ! -z "$S3_BUCKET" ]]; then
    # Download from S3
    S3_PATH="s3://$S3_BUCKET/$S3_PREFIX/$ENV/$TIMESTAMP.tar.gz"
    BACKUP_FILE="$BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz"

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
      echo -e "${RED}Error: AWS CLI not found${NC}"
      exit 1
    fi

    echo -e "${YELLOW}Downloading backup from S3: $S3_PATH${NC}"
    if ! $DRY_RUN; then
      mkdir -p "$BACKUP_DIR"
      aws s3 cp "$S3_PATH" "$BACKUP_FILE"
    else
      echo -e "${YELLOW}[DRY RUN] aws s3 cp $S3_PATH $BACKUP_FILE${NC}"
    fi
  else
    BACKUP_FILE="$BACKUP_DIR/$ENV-$TIMESTAMP.tar.gz"
  fi
fi

# Check if backup file exists
if [[ ! -f "$BACKUP_FILE" && ! $DRY_RUN ]]; then
  echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
  exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  QuantumAlpha Restore ($ENV)            ${NC}"
echo -e "${BLUE}  Backup file: $BACKUP_FILE              ${NC}"
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

# Confirm restore
if [[ "$FORCE" != true ]]; then
  echo -e "${YELLOW}WARNING: This will overwrite existing data. Are you sure you want to continue? (y/N)${NC}"
  read -r CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo -e "${RED}Restore aborted${NC}"
    exit 1
  fi
fi

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
echo -e "${GREEN}✓ Created temporary directory: $TEMP_DIR${NC}"

# Extract backup
echo -e "\n${YELLOW}Extracting backup...${NC}"
EXTRACT_CMD="tar -xzf $BACKUP_FILE -C $TEMP_DIR"
execute_cmd "$EXTRACT_CMD"
echo -e "${GREEN}✓ Backup extracted${NC}"

# Get timestamp from extracted directory
EXTRACTED_TIMESTAMP=$(ls "$TEMP_DIR")
RESTORE_PATH="$TEMP_DIR/$EXTRACTED_TIMESTAMP"

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
      echo -e "\n${YELLOW}Restoring PostgreSQL database...${NC}"

      # Check if PostgreSQL backup exists
      if [[ ! -d "$RESTORE_PATH/postgres" && ! $DRY_RUN ]]; then
        echo -e "${YELLOW}Warning: PostgreSQL backup not found in the archive${NC}"
        continue
      fi

      # Set default values if not in environment
      DB_HOST=${DB_HOST:-localhost}
      DB_PORT=${DB_PORT:-5432}
      DB_USERNAME=${DB_USERNAME:-postgres}
      DB_PASSWORD=${DB_PASSWORD:-postgres}
      DB_NAME=${DB_NAME:-quantumalpha}

      # Set PGPASSWORD environment variable
      export PGPASSWORD="$DB_PASSWORD"

      # Check if database exists
      DB_EXISTS_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -lqt | cut -d \\| -f 1 | grep -qw $DB_NAME"

      if $DRY_RUN; then
        echo -e "${YELLOW}[DRY RUN] Checking if database exists: $DB_NAME${NC}"
      else
        if eval $DB_EXISTS_CMD; then
          echo -e "${YELLOW}Database exists: $DB_NAME${NC}"

          # Drop connections to the database
          DROP_CONN_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();\" postgres"
          execute_cmd "$DROP_CONN_CMD"

          # Drop database
          DROP_DB_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -c \"DROP DATABASE $DB_NAME;\" postgres"
          execute_cmd "$DROP_DB_CMD"
        else
          echo -e "${YELLOW}Database does not exist: $DB_NAME${NC}"
        fi

        # Create database
        CREATE_DB_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -c \"CREATE DATABASE $DB_NAME;\" postgres"
        execute_cmd "$CREATE_DB_CMD"
      fi

      # Restore full database
      if [[ -f "$RESTORE_PATH/postgres/full_backup.dump" || $DRY_RUN ]]; then
        RESTORE_CMD="pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME -v $RESTORE_PATH/postgres/full_backup.dump"
        execute_cmd "$RESTORE_CMD"
      else
        # Restore schema
        if [[ -f "$RESTORE_PATH/postgres/schema.sql" || $DRY_RUN ]]; then
          SCHEMA_RESTORE_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME -f $RESTORE_PATH/postgres/schema.sql"
          execute_cmd "$SCHEMA_RESTORE_CMD"
        fi

        # Restore data
        if [[ -f "$RESTORE_PATH/postgres/data.sql" || $DRY_RUN ]]; then
          DATA_RESTORE_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME -f $RESTORE_PATH/postgres/data.sql"
          execute_cmd "$DATA_RESTORE_CMD"
        fi
      fi

      # Clear PGPASSWORD
      unset PGPASSWORD

      echo -e "${GREEN}✓ PostgreSQL restore completed${NC}"
      ;;

    influxdb)
      echo -e "\n${YELLOW}Restoring InfluxDB...${NC}"

      # Check if InfluxDB backup exists
      if [[ ! -d "$RESTORE_PATH/influxdb" && ! $DRY_RUN ]]; then
        echo -e "${YELLOW}Warning: InfluxDB backup not found in the archive${NC}"
        continue
      fi

      # Set default values if not in environment
      INFLUXDB_URL=${INFLUXDB_URL:-http://localhost:8086}
      INFLUXDB_ORG=${INFLUXDB_ORG:-quantumalpha}
      INFLUXDB_TOKEN=${INFLUXDB_TOKEN:-}
      INFLUXDB_BUCKET=${INFLUXDB_BUCKET:-market_data}

      # Check if influx CLI is installed
      if ! command -v influx &> /dev/null; then
        echo -e "${YELLOW}Warning: influx CLI not found. Using Docker for restore.${NC}"

        # Use Docker to restore InfluxDB
        INFLUX_RESTORE_CMD="docker run --rm \
          -v $RESTORE_PATH/influxdb:/backup \
          -e INFLUX_HOST=$INFLUXDB_URL \
          -e INFLUX_ORG=$INFLUXDB_ORG \
          -e INFLUX_TOKEN=$INFLUXDB_TOKEN \
          influxdb:2.0 \
          influx restore /backup --bucket $INFLUXDB_BUCKET"
        execute_cmd "$INFLUX_RESTORE_CMD"
      else
        # Use influx CLI directly
        INFLUX_RESTORE_CMD="influx restore $RESTORE_PATH/influxdb --host $INFLUXDB_URL --org $INFLUXDB_ORG --token $INFLUXDB_TOKEN --bucket $INFLUXDB_BUCKET"
        execute_cmd "$INFLUX_RESTORE_CMD"
      fi

      echo -e "${GREEN}✓ InfluxDB restore completed${NC}"
      ;;

    config)
      echo -e "\n${YELLOW}Restoring configuration files...${NC}"

      # Check if config backup exists
      if [[ ! -d "$RESTORE_PATH/config" && ! $DRY_RUN ]]; then
        echo -e "${YELLOW}Warning: Configuration backup not found in the archive${NC}"
        continue
      fi

      # Backup current config
      CURRENT_CONFIG_BACKUP="$PROJECT_ROOT/config.bak"
      BACKUP_CURRENT_CMD="mv $PROJECT_ROOT/config $CURRENT_CONFIG_BACKUP"
      execute_cmd "$BACKUP_CURRENT_CMD"

      # Create config directory
      MKDIR_CMD="mkdir -p $PROJECT_ROOT/config"
      execute_cmd "$MKDIR_CMD"

      # Restore config
      RESTORE_CONFIG_CMD="cp -r $RESTORE_PATH/config/* $PROJECT_ROOT/config/"
      execute_cmd "$RESTORE_CONFIG_CMD"

      echo -e "${GREEN}✓ Configuration restore completed${NC}"
      echo -e "${YELLOW}Note: Original configuration backed up to $CURRENT_CONFIG_BACKUP${NC}"
      ;;

    *)
      echo -e "${RED}Error: Unknown component: $COMPONENT${NC}"
      echo "Available components: postgres, influxdb, config"
      ;;
  esac
done

# Clean up
echo -e "\n${YELLOW}Cleaning up...${NC}"
CLEANUP_CMD="rm -rf $TEMP_DIR"
execute_cmd "$CLEANUP_CMD"
echo -e "${GREEN}✓ Temporary files cleaned up${NC}"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  QuantumAlpha Restore Completed         ${NC}"
echo -e "${GREEN}=========================================${NC}"
