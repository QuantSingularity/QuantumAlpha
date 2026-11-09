# Installation Guide

## Overview

This guide covers installation of QuantumAlpha on multiple platforms including local development, Docker, and cloud deployment.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Environment Configuration](#environment-configuration)
- [Verification](#verification)
- [Next Steps](#next-steps)

---

## Prerequisites

### System Requirements

| Component          | Minimum                                                 | Recommended                                |
| ------------------ | ------------------------------------------------------- | ------------------------------------------ |
| **OS**             | Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+ (WSL2) | Ubuntu 22.04 LTS                           |
| **Python**         | 3.10                                                    | 3.11+                                      |
| **RAM**            | 8 GB                                                    | 16 GB+                                     |
| **CPU**            | 4 cores                                                 | 8+ cores                                   |
| **GPU**            | None (CPU-only)                                         | NVIDIA GPU with CUDA 11.8+ for ML training |
| **Storage**        | 20 GB                                                   | 50 GB+ SSD                                 |
| **Docker**         | 20.10+                                                  | Latest stable                              |
| **Docker Compose** | 2.0+                                                    | Latest stable                              |
| **Node.js**        | 16.x                                                    | 18.x+ (for frontend development)           |

### Required Software

Before installation, ensure you have:

```bash
# Check Python version (required: 3.10+)
python3 --version

# Check Docker
docker --version

# Check Docker Compose
docker-compose --version

# Optional: Check Node.js (for frontend)
node --version
npm --version
```

---

## Installation Methods

QuantumAlpha supports three installation methods:

| Method                   | Use Case                            | Difficulty | Time      |
| ------------------------ | ----------------------------------- | ---------- | --------- |
| **Docker (Recommended)** | Production, testing, quick start    | Easy       | 10-15 min |
| **Development Setup**    | Active development, debugging       | Moderate   | 20-30 min |
| **Manual Installation**  | Custom environments, advanced users | Advanced   | 30-45 min |

---

## Platform-Specific Instructions

### Docker Installation (Recommended)

Docker installation is the fastest way to get QuantumAlpha running.

| OS / Platform             | Recommended install command                                  | Notes                                        |
| ------------------------- | ------------------------------------------------------------ | -------------------------------------------- |
| **Linux**                 | `./scripts/setup_env.sh && docker-compose up`                | Requires Docker and Docker Compose installed |
| **macOS**                 | `./scripts/setup_env.sh && docker-compose up`                | Docker Desktop required                      |
| **Windows (WSL2)**        | `bash ./scripts/setup_env.sh && docker-compose up`           | WSL2 with Docker Desktop                     |
| **Cloud (AWS/GCP/Azure)** | Use Kubernetes deployment (see `infrastructure/kubernetes/`) | Terraform templates provided                 |

#### Step-by-Step Docker Installation

```bash
# 1. Clone the repository
git clone https://github.com/quantsingularity/QuantumAlpha.git
cd QuantumAlpha

# 2. Set up environment (creates .env file and checks dependencies)
./scripts/setup_env.sh

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

**Access Points:**

- Dashboard: <http://localhost:3000>
- API Gateway: <http://localhost:8080>
- API Documentation: <http://localhost:8080/api-docs>
- Prometheus Metrics: <http://localhost:9090>
- Grafana Dashboard: <http://localhost:3001>

---

### Development Setup

For active development and debugging:

```bash
# 1. Clone the repository
git clone https://github.com/quantsingularity/QuantumAlpha.git
cd QuantumAlpha

# 2. Run setup script (creates virtual environment)
./scripts/setup_env.sh --env dev

# 3. Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# 4. Install backend dependencies
cd backend
pip install -r requirements.txt

# 5. Install frontend dependencies
cd ../web-frontend
npm install

# 6. Start infrastructure services
docker-compose up postgres redis kafka zookeeper influxdb mongodb -d

# 7. Start development server
cd ../scripts
./start_dev.sh
```

---

### Manual Installation

For custom or minimal environments:

```bash
# 1. Install Python dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. Install Node.js dependencies (frontend)
cd ../web-frontend
npm install

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# 4. Initialize database
cd ../scripts
python setup_db.py

# 5. Start services individually
cd ../backend
python app.py  # Main API Gateway

# In separate terminals:
python ai_engine/app.py
python data_service/app.py
python risk_service/app.py
python execution_service/app.py

# 6. Start frontend
cd ../web-frontend
npm start
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantumalpha_db
DB_USER=quantumalpha_user
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=quantumalpha

# InfluxDB Configuration (Time Series Data)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=quantumalpha
INFLUXDB_BUCKET=market_data

# API Keys (Data Providers)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key

# Broker Integration
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # paper trading

# AI/ML Configuration
MODEL_REGISTRY_PATH=./backend/models
FEATURE_STORE_PATH=./backend/features
EXPERIMENT_TRACKING_URI=http://localhost:5000  # MLflow
ENABLE_REINFORCEMENT_LEARNING=false

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Security
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
FLASK_SECRET_KEY=your_flask_secret_key_change_in_production

# Application
FLASK_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Optional Configuration Files

Configuration files in `backend/config_files/`:

- `services/ai_engine.yaml` - AI model parameters
- `services/data_service.yaml` - Data ingestion settings
- `services/execution_service.yaml` - Execution strategies
- `services/risk_service.yaml` - Risk parameters
- `database/postgres.yaml` - Database connection pools
- `database/influxdb.yaml` - Time series retention policies

---

## Verification

### Verify Installation

```bash
# 1. Check all services are running
docker-compose ps
# All services should show "Up" status

# 2. Test API Gateway health
curl http://localhost:8080/health

# Expected response:
# {"status": "ok", "service": "api_gateway"}

# 3. Test individual services
curl http://localhost:8081/health  # Data Service
curl http://localhost:8082/health  # AI Engine
curl http://localhost:8083/health  # Risk Service
curl http://localhost:8084/health  # Execution Service

# 4. Access dashboard
# Open browser to http://localhost:3000

# 5. Run basic tests
cd tests
pytest tests/integration/test_basic_health.py
```

### Common Installation Issues

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions to common problems.

---

## Next Steps

After successful installation:

1. **Configure API Keys**: Add your data provider API keys to `.env`
2. **Read Usage Guide**: See [USAGE.md](./USAGE.md) for basic workflows
3. **Explore API**: Check [API.md](./API.md) for endpoint documentation
4. **Run Examples**: Try examples in [examples/](./examples/) directory
5. **Review Architecture**: Understand the system in [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Upgrading

To upgrade to a new version:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild Docker images
docker-compose build --no-cache

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Run database migrations if needed
docker-compose exec backend python scripts/migrate_db.py
```

---

## Uninstallation

To completely remove QuantumAlpha:

```bash
# 1. Stop and remove containers
docker-compose down -v

# 2. Remove Docker images
docker rmi $(docker images | grep quantumalpha | awk '{print $3}')

# 3. Remove project directory
cd ..
rm -rf QuantumAlpha

# 4. (Optional) Remove virtual environment
rm -rf venv
```
