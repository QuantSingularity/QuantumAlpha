# QuantumAlpha - Advanced AI Hedge Fund Platform

![CI/CD Pipeline](https://github.com/quantsingularity/quantumalpha/actions/workflows/cicd.yml/badge.svg)
[![Test Coverage](https://img.shields.io/badge/coverage-78%25-yellow)](https://github.com/quantsingularity/QuantumAlpha/tests)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/quantsingularity/QuantumAlpha/LICENSE)

![QuantumAlpha Dashboard](docs/images/dashboard.bmp)

> **Note**: This project is under active development. Features and functionalities are continuously being enhanced to improve trading performance, risk management, and user experience.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation and Setup](#installation-and-setup)
- [Best Practices](#best-practices)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

QuantumAlpha is a high-performance, AI-driven quantitative trading platform that ingests market and alternative data, trains advanced ML models, and executes strategies with low-latency execution. Built on microservices and an event-driven architecture, it provides model lifecycle management, robust risk controls, smart order routing, and real-time monitoring to generate and protect alpha.

---

## Project Structure

The project is organized into several main components:

```
QuantumAlpha/
├── code/                   # Core backend logic, services, and shared utilities
├── docs/                   # Project documentation
├── infrastructure/         # DevOps, deployment, and infra-related code
├── mobile-frontend/        # Mobile application
├── web-frontend/           # Web dashboard
├── scripts/                # Automation, setup, and utility scripts
├── LICENSE                 # License information
├── README.md               # Project overview and instructions
└── tools/                  # Formatter configs, linting tools, and dev utilities
```

## Key Features

QuantumAlpha's functionality is structured around five core pillars of a modern quantitative trading system.

### AI-Driven Trading Strategies

The platform's alpha generation relies on sophisticated AI models:

- **Machine Learning (ML) and Deep Learning Models**: Predict market movements using time-series models such as **LSTM/GRU networks** and **Transformer architectures**.
- **Reinforcement Learning (RL)**: Trains agents (e.g., Deep Q-Networks, PPO, or Actor-Critic methods) to make trade and portfolio decisions via simulated reward maximization.
- **Model Robustness**: Employs ensemble and meta-learning techniques, alongside online learning, to enhance model stability.
- **Explainable AI (XAI)**: Provides model interpretability through SHAP plots and feature importance bars per trade.

### Alternative Data Processing

Leveraging non-traditional data sources for an edge:

- **Sentiment Analysis**: Processes news and social media sentiment using NLP transformers.
- **Geospatial Data**: Utilizes satellite imagery analysis for insights into commodity markets.
- **Supply Chain Indicators**: Automated feature extraction from web-scraped data using techniques like PCA or autoencoders.
- **Data Fusion**: Combines structured market data (prices, volumes) with unstructured alternative data for comprehensive signal generation.

### Risk Management System

A robust framework for capital preservation and risk control:

- **Risk Assessment**: Uses **Bayesian Value at Risk (VaR)** for probabilistic risk assessment.
- **Stress Testing**: Implements a scenario-based framework for evaluating risk under extreme market conditions.
- **Position Sizing**: Optimizes capital allocation using the **Kelly criterion** and risk parity approaches.
- **Continuous Monitoring**: Provides real-time risk metrics and alerts to ensure compliance with risk limits.

### Execution Engine

Optimizing trade execution for minimal market impact:

- **Smart Order Routing (SOR)**: Ensures optimal execution across multiple trading venues.
- **Adaptive Algorithms**: Features TWAP, VWAP, and ML-enhanced variants of execution algorithms.
- **Market Impact Modeling**: Includes Transaction Cost Analysis (TCA) to minimize trading costs.
- **High-Frequency Capabilities**: Designed for sub-millisecond order management.

### Data Pipeline & Monitoring

Managing the flow and visibility of critical information:

- **Data Ingestion**: Collects market data, fundamentals, and alternative sources via real-time and batch pipelines, often utilizing **Apache Kafka** or cloud pub/sub platforms.
- **Historical Data**: Efficient storage and retrieval of time-series data for backtesting and training.
- **Feature Engineering**: Automated feature extraction and selection for model inputs.
- **Real-time Dashboard**: Provides comprehensive monitoring of P&L charts, risk metrics, strategy controls, and audit logs.

---

## Architecture

QuantumAlpha follows a microservices architecture, with components logically grouped into layers for clear separation of concerns, scalability, and resilience.

### Architectural Components

The system is divided into five primary layers:

| Layer                     | Key Components                                                                                                  | Function                                                                                                                           |
| :------------------------ | :-------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Data Layer**            | Market Data Collectors, Alternative Data Processors, Feature Engineering Pipeline, Data Storage                 | Ingests, processes, and stores all market and alternative data for the platform.                                                   |
| **AI Engine**             | Model Training Service, Prediction Service, Reinforcement Learning Environment, Model Registry                  | Manages the entire ML lifecycle, from distributed training and hyperparameter tuning to real-time inference and signal generation. |
| **Risk Management**       | Portfolio Construction, Risk Calculation Service (VaR, stress testing), Position Sizing, Risk Monitoring        | Calculates, monitors, and manages portfolio risk and optimal capital allocation.                                                   |
| **Execution Layer**       | Order Management System (OMS), Execution Algorithms (SOR, TWAP, VWAP), Broker Connectivity, Post-Trade Analysis | Manages the lifecycle of trade orders, from signal generation to final execution and cost analysis.                                |
| **Frontend Applications** | Admin Dashboard, Analytics Interface, Configuration Portal, Documentation Hub                                   | Provides user interfaces for strategy monitoring, performance visualization, and system configuration.                             |

### Event-Driven Communication

The platform relies on an event-driven architecture for low-latency, asynchronous communication between services:

1.  **Market Events**: Price updates, order book changes, and trade executions.
2.  **Signal Events**: Model predictions and trading signals generated by the AI Engine.
3.  **Order Events**: Order creation, updates, and execution reports from the Execution Layer.
4.  **System Events**: Infrastructure scaling and monitoring alerts.

---

## Technology Stack

The platform is built with a polyglot technology stack optimized for high performance and quantitative finance requirements.

### Core Technologies

| Category                | Key Technologies                                                    | Description                                                                                              |
| :---------------------- | :------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------- |
| **Languages**           | Python, C++                                                         | Python for ML/data processing; C++ for performance-critical components (e.g., high-frequency execution). |
| **ML Frameworks**       | PyTorch, TensorFlow, scikit-learn, Ray                              | Comprehensive suite for deep learning, traditional ML, and distributed computing.                        |
| **Data Processing**     | Pandas, NumPy, Dask, Apache Spark                                   | Libraries for efficient data manipulation, large-scale data processing, and distributed computing.       |
| **Financial Libraries** | QuantLib, Backtrader/zipline, PyPortfolioOpt                        | Specialized tools for quantitative finance, backtesting, and portfolio optimization.                     |
| **Data Storage**        | InfluxDB (time series), PostgreSQL (relational), MongoDB (document) | Polyglot persistence strategy for specialized data types.                                                |
| **Streaming**           | Kafka, Redis Streams                                                | High-throughput message brokers for real-time data ingestion and event management.                       |

### Frontend & Infrastructure

| Category             | Key Technologies                                                     | Description                                                                                                  |
| :------------------- | :------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Frontend**         | React, TypeScript, D3.js, Plotly, Redux Toolkit, Material-UI         | Modern stack for a responsive, data-intensive web dashboard with advanced visualization capabilities.        |
| **Containerization** | Docker, Kubernetes                                                   | Ensures deployment flexibility, service mesh capabilities, and GitOps-based continuous delivery.             |
| **DevOps & MLOps**   | GitHub Actions, AWS/GCP, Prometheus, Grafana, ELK Stack, MLflow, DVC | Automated CI/CD, multi-cloud deployment, full observability, and MLOps tools for model lifecycle management. |

---

## Installation and Setup

### Prerequisites

To set up the platform, ensure you have the following installed:

- **Python** (v3.10+)
- **Docker** and Docker Compose
- **Node.js** (v16+)
- **C++ compiler** (required for QuantLib and other libraries)
- **CUDA-compatible GPU** (highly recommended for ML training)

### Quick Setup

The fastest way to get the development environment running is using the provided script:

| Step                     | Command                                                                             | Description                                                     |
| :----------------------- | :---------------------------------------------------------------------------------- | :-------------------------------------------------------------- |
| **1. Clone Repository**  | `git clone https://github.com/quantsingularity/QuantumAlpha.git && cd QuantumAlpha` | Download the source code and navigate to the project directory. |
| **2. Run Setup Script**  | `./setup_env.sh`                                                                    | Installs dependencies and configures the local environment.     |
| **3. Start Application** | `docker-compose up`                                                                 | Starts all core services, databases, and the API Gateway.       |

**Access Points:**

- **Dashboard**: `http://localhost:3000`
- **API Gateway**: `http://localhost:8080`
- **Swagger Documentation**: `http://localhost:8080/api-docs`

### Manual Setup

For manual setup, you must first configure the necessary environment variables in a `.env` file, including database credentials, API keys for data providers (Alpha Vantage, Polygon), and broker configurations (e.g., Alpaca). Individual services must then be started using their respective commands (e.g., `python main.py` for Python services, `npm start` for the frontend).

---

## Best Practices

The development and operation of QuantumAlpha adhere to strict best practices for quantitative systems:

- **Version Control**: Rigorous version control for both code and data using **DVC** and **MLflow**.
- **Testing**: Comprehensive unit and integration tests for strategy logic and risk calculations.
- **Safety**: Deployment of **"kill-switch" mechanisms** to halt trading if risk metrics exceed predefined thresholds.
- **Monitoring**: Continuous review of model outputs for regime shifts or performance degradation.
- **Documentation**: Thorough documentation of all models, data sources, and system components.
- **Reproducibility**: Emphasis on reproducible research and trading strategies.

---

## Testing

QuantumAlpha maintains approximately **78% test coverage** across the platform, utilizing a comprehensive testing strategy to ensure reliability and performance.

### Testing Strategy

| Test Type             | Description                                                                 | Purpose                                                                         |
| :-------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **Unit Tests**        | Individual components and functions tested in isolation.                    | Verifies correctness of core logic (e.g., signal generation, risk calculation). |
| **Integration Tests** | Interactions between services (e.g., Data Layer to AI Engine).              | Ensures components work together seamlessly.                                    |
| **System Tests**      | End-to-end workflows (e.g., signal to execution).                           | Validates critical user and trading journeys.                                   |
| **Backtests**         | Historical performance validation using the Event-Driven Simulator.         | Evaluates strategy profitability and robustness over time.                      |
| **Stress Tests**      | System behavior under extreme conditions (e.g., high-volume market events). | Confirms system resilience and capacity limits.                                 |

### Running Tests

Tests are executed using `pytest` for the backend and `Jest`/`Cypress` for the frontend.

| Test Scope            | Command Example                                   |
| :-------------------- | :------------------------------------------------ |
| **All Backend Tests** | `pytest`                                          |
| **Specific Category** | `pytest tests/unit` or `pytest tests/integration` |
| **Coverage Report**   | `pytest --cov=src tests/`                         |

---

## CI/CD Pipeline

QuantumAlpha uses GitHub Actions for continuous integration and deployment:

| Stage                | Control Area                    | Institutional-Grade Detail                                                              |
| :------------------- | :------------------------------ | :-------------------------------------------------------------------------------------- |
| **Formatting Check** | Change Triggers                 | Enforced on all `push` and `pull_request` events to `main` and `develop`                |
|                      | Manual Oversight                | On-demand execution via controlled `workflow_dispatch`                                  |
|                      | Source Integrity                | Full repository checkout with complete Git history for auditability                     |
|                      | Python Runtime Standardization  | Python 3.10 with deterministic dependency caching                                       |
|                      | Backend Code Hygiene            | `autoflake` to detect unused imports/variables using non-mutating diff-based validation |
|                      | Backend Style Compliance        | `black --check` to enforce institutional formatting standards                           |
|                      | Non-Intrusive Validation        | Temporary workspace comparison to prevent unauthorized source modification              |
|                      | Node.js Runtime Control         | Node.js 18 with locked dependency installation via `npm ci`                             |
|                      | Web Frontend Formatting Control | Prettier checks for web-facing assets                                                   |
|                      | Mobile Frontend Formatting      | Prettier enforcement for mobile application codebases                                   |
|                      | Documentation Governance        | Repository-wide Markdown formatting enforcement                                         |
|                      | Infrastructure Configuration    | Prettier validation for YAML/YML infrastructure definitions                             |
|                      | Compliance Gate                 | Any formatting deviation fails the pipeline and blocks merge                            |

---

## Documentation

| Document                    | Path                 | Description                                                    |
| :-------------------------- | :------------------- | :------------------------------------------------------------- |
| **README**                  | `README.md`          | High-level overview, project scope, and repository entry point |
| **Installation Guide**      | `INSTALLATION.md`    | Step-by-step installation and environment setup                |
| **API Reference**           | `API.md`             | Detailed documentation for all API endpoints                   |
| **CLI Reference**           | `CLI.md`             | Command-line interface usage, commands, and examples           |
| **User Guide**              | `USAGE.md`           | Comprehensive end-user guide, workflows, and examples          |
| **Architecture Overview**   | `ARCHITECTURE.md`    | System architecture, components, and design rationale          |
| **Configuration Guide**     | `CONFIGURATION.md`   | Configuration options, environment variables, and tuning       |
| **Feature Matrix**          | `FEATURE_MATRIX.md`  | Feature coverage, capabilities, and roadmap alignment          |
| **Contributing Guidelines** | `CONTRIBUTING.md`    | Contribution workflow, coding standards, and PR requirements   |
| **Troubleshooting**         | `TROUBLESHOOTING.md` | Common issues, diagnostics, and remediation steps              |

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
