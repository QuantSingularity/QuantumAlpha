# Troubleshooting Guide

## Overview

Common issues and solutions for QuantumAlpha platform.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Service Startup Problems](#service-startup-problems)
- [Database Connection Issues](#database-connection-issues)
- [API Errors](#api-errors)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)

---

## Installation Issues

### Python Version Mismatch

**Problem:** `ERROR: Python 3.10+ required`

**Solution:**

```bash
# Check Python version
python3 --version

# Install Python 3.10+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3.10-venv

# Create virtual environment with specific version
python3.10 -m venv venv
```

### Missing System Dependencies

**Problem:** `error: command 'gcc' failed`

**Solution:**

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev libpq-dev

# macOS
xcode-select --install
brew install postgresql
```

### Docker Not Running

**Problem:** `Cannot connect to Docker daemon`

**Solution:**

```bash
# Linux
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in

# macOS
open -a Docker

# Verify
docker info
```

---

## Service Startup Problems

### Port Already in Use

**Problem:** `Error: Port 8080 already in use`

**Solution:**

```bash
# Find process using port
lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill process
kill -9 "$PID"  # PID from the output above

# Or use different port
./scripts/start_service.sh --service ai_engine --port 9000
```

### Environment Variables Not Set

**Problem:** `KeyError: 'DB_PASSWORD'`

**Solution:**

```bash
# Check if .env file exists
ls -la .env

# Copy example file
cp .env.example .env

# Edit with your values
nano .env

# Verify variables are set
source .env
echo $DB_PASSWORD
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Verify installation
pip list | grep Flask
```

---

## Database Connection Issues

### PostgreSQL Connection Refused

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Start PostgreSQL
docker-compose up -d postgres

# Check logs
docker-compose logs postgres

# Test connection
psql -h localhost -U quantumalpha_user -d quantumalpha_db
```

### Database Does Not Exist

**Problem:** `FATAL: database "quantumalpha_db" does not exist`

**Solution:**

```bash
# Initialize database
python scripts/setup_db.py

# Or manually create
docker-compose exec postgres psql -U postgres
CREATE DATABASE quantumalpha_db;
\q
```

### Redis Connection Failed

**Problem:** `redis.exceptions.ConnectionError: Connection refused`

**Solution:**

```bash
# Start Redis
docker-compose up -d redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Redis host/port in .env
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

---

## API Errors

### 401 Unauthorized

**Problem:** `{"error": "Unauthorized", "status_code": 401}`

**Solution:**

```bash
# Get new access token
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8080/api/models
```

### 404 Not Found

**Problem:** `{"error": "Not Found", "status_code": 404}`

**Solution:**

```bash
# Check correct URL
# API Gateway: http://localhost:8080/api/v1/...
# Direct service: http://localhost:8082/api/...

# Verify service is running
curl http://localhost:8082/health

# Check API documentation
curl http://localhost:8080/api-docs
```

### 429 Rate Limit Exceeded

**Problem:** `{"error": "Too Many Requests", "status_code": 429}`

**Solution:**

- Wait for rate limit window to reset (check `X-RateLimit-Reset` header)
- Implement exponential backoff
- Request rate limit increase if needed
- Use batch APIs when available

### 500 Internal Server Error

**Problem:** `{"error": "Internal Server Error", "status_code": 500}`

**Solution:**

```bash
# Check service logs
docker-compose logs ai_engine

# Look for Python tracebacks
# Common causes:
# - Missing configuration
# - Invalid input data
# - Database connection issues
# - Out of memory

# Restart service
docker-compose restart ai_engine
```

---

## Performance Issues

### Slow API Responses

**Problem:** API calls taking >5 seconds

**Diagnosis:**

```bash
# Check service resource usage
docker stats

# Check database queries
docker-compose exec postgres psql -U postgres -d quantumalpha_db
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Check Redis cache hit rate
docker-compose exec redis redis-cli info stats
```

**Solutions:**

```bash
# Enable caching
# Set REDIS_CACHE_TTL=3600 in .env

# Add database indexes
# See scripts/optimize_db.sql

# Increase worker processes
# Update gunicorn workers in docker-compose.yml
```

### High Memory Usage

**Problem:** Services consuming >4GB RAM

**Solution:**

```bash
# Limit Docker container memory
# In docker-compose.yml:
services:
  ai_engine:
    deploy:
      resources:
        limits:
          memory: 2G

# Reduce batch sizes
# In ai_engine.yaml:
hyperparameters:
  batch_size: 32  # Reduce from 64

# Clear model cache
rm -rf backend/models/cache/
```

### ML Model Training Timeout

**Problem:** Model training takes >2 hours

**Solution:**

```text
# Reduce epochs
"epochs": 50  # Instead of 100

# Use smaller model
"lstm_units": 64  # Instead of 128

# Enable GPU acceleration
# Set GPU_ENABLED=true in .env

# Use distributed training (Ray)
```

---

## Docker Issues

### Container Fails to Start

**Problem:** `Container exited with code 1`

**Solution:**

```bash
# Check logs
docker-compose logs "$SERVICE_NAME"  # name of the failing service

# Common issues:
# 1. Syntax error in code
# 2. Missing dependencies
# 3. Port conflict
# 4. Volume mount issues

# Rebuild container
docker-compose build --no-cache "$SERVICE_NAME"
docker-compose up -d "$SERVICE_NAME"
```

### Volume Permission Errors

**Problem:** `Permission denied: '/var/lib/postgresql/data'`

**Solution:**

```bash
# Fix ownership
sudo chown -R $USER:$USER ./data

# Or use named volumes (recommended)
# In docker-compose.yml:
volumes:
  postgres_data:
```

### Out of Disk Space

**Problem:** `no space left on device`

**Solution:**

```bash
# Check disk usage
df -h

# Remove unused Docker resources
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Clean up logs
docker-compose down
sudo rm -rf /var/lib/docker/containers/*/*-json.log
```

---

## Common Error Messages

### "Model not found"

**Cause:** Model ID doesn't exist or was deleted

**Solution:**

```bash
# List available models
curl http://localhost:8082/api/models

# Train new model
curl -X POST http://localhost:8082/api/train-model \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "type": "lstm", ...}'
```

### "Invalid input data"

**Cause:** Request body doesn't match schema

**Solution:**

```bash
# Check API documentation for required fields
curl http://localhost:8080/api-docs

# Validate JSON schema
# See backend/common/validation.py

# Example valid request:
{
  "symbol": "AAPL",      # Required
  "data": [...],         # Required
  "model_id": "model_123"  # Optional
}
```

### "Database migration required"

**Cause:** Database schema out of date

**Solution:**

```bash
# Run migrations
python scripts/migrate_db.py

# Or reset database
docker-compose down -v
docker-compose up -d
python scripts/setup_db.py
```

---

## Getting Help

If you can't resolve the issue:

1. **Check logs**: `docker-compose logs -f`
2. **Search issues**: <https://github.com/quantsingularity/QuantumAlpha/issues>
3. **Ask for help**: Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment info (`docker --version`, `python --version`)
   - Relevant logs

---

## Debug Mode

Enable debug logging:

```bash
# In .env file
FLASK_ENV=development
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart

# View debug logs
docker-compose logs -f ai_engine | grep DEBUG
```

---

**See Also:**

- [INSTALLATION.md](./INSTALLATION.md) - Setup guide
- [CONFIGURATION.md](./CONFIGURATION.md) - Configuration options
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guide
