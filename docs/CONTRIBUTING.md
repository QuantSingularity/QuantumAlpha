# Contributing Guide

## Overview

Thank you for considering contributing to QuantumAlpha! This document provides guidelines for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers
- Respect differing viewpoints
- Report unacceptable behavior to maintainers

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/quantsingularity/QuantumAlpha.git
cd QuantumAlpha

# Add upstream remote
git remote add upstream https://github.com/quantsingularity/QuantumAlpha.git
```

### 2. Set Up Development Environment

```bash
# Run setup script
./scripts/setup_env.sh --env dev

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# OR
git checkout -b fix/your-bug-fix
```

---

## Development Workflow

### Branch Naming Conventions

| Type          | Pattern                | Example                     |
| ------------- | ---------------------- | --------------------------- |
| Feature       | `feature/description`  | `feature/add-lstm-model`    |
| Bug fix       | `fix/description`      | `fix/order-validation`      |
| Documentation | `docs/description`     | `docs/update-api-reference` |
| Refactoring   | `refactor/description` | `refactor/risk-calculator`  |
| Performance   | `perf/description`     | `perf/optimize-queries`     |

### Commit Message Format

Use conventional commits:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**

```text
feat(ai-engine): add BERT sentiment analysis model

Implement FinBERT-based sentiment analysis for news articles.
Includes training pipeline and inference API endpoint.

Closes #123
```

---

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

```python
# Line length: 88 characters (Black default)
# Use type hints
def calculate_risk(portfolio: Dict[str, Any], confidence: float = 0.95) -> Dict[str, float]:
    """Calculate portfolio risk metrics.

    Args:
        portfolio: Portfolio positions
        confidence: VaR confidence level (default: 0.95)

    Returns:
        Dictionary of risk metrics
    """
    pass

# Use descriptive variable names
portfolio_value = sum(position.value for position in positions)

# Import order: standard library, third-party, local
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from flask import Flask, jsonify

from backend.common.config import get_config_manager
```

### Code Formatting Tools

```bash
# Format Python code with Black
black backend/

# Sort imports
isort backend/

# Check code quality
flake8 backend/

# Type checking
mypy backend/
```

### JavaScript/TypeScript Style

```typescript
// Use TypeScript for type safety
interface Order {
  orderId: string;
  symbol: string;
  quantity: number;
  status: OrderStatus;
}

// Use arrow functions
const calculateTotal = (orders: Order[]): number => {
  return orders.reduce((sum, order) => sum + order.quantity, 0);
};

// Use descriptive names
const fetchMarketData = async (symbol: string): Promise<MarketData> => {
  // Implementation
};
```

---

## Testing Requirements

### Test Coverage Goals

- **Minimum coverage: 70%**
- **Target coverage: 80%+**
- All new features must include tests
- Bug fixes must include regression tests

### Writing Tests

```python
# tests/unit/ai_engine/test_model_manager.py
import pytest
from backend.ai_engine.model_manager import ModelManager

def test_create_model_success(mock_config, mock_db):
    """Test successful model creation."""
    manager = ModelManager(mock_config, mock_db)

    model_data = {
        "name": "test_model",
        "type": "lstm",
        "parameters": {"lstm_units": 128}
    }

    model = manager.create_model(model_data)

    assert model["name"] == "test_model"
    assert model["status"] == "created"
    assert "id" in model

def test_create_model_missing_name(mock_config, mock_db):
    """Test model creation fails without name."""
    manager = ModelManager(mock_config, mock_db)

    with pytest.raises(ValidationError):
        manager.create_model({"type": "lstm"})
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/ai_engine/test_model_manager.py

# Run with coverage
pytest --cov=backend tests/

# Run specific test
pytest tests/unit/ai_engine/test_model_manager.py::test_create_model_success

# Run in verbose mode
pytest -v
```

---

## Documentation Standards

### Code Documentation

```python
def calculate_position_size(
    signal_strength: float,
    portfolio_value: float,
    risk_tolerance: float,
    volatility: float
) -> Dict[str, float]:
    """Calculate optimal position size using Kelly Criterion.

    The Kelly Criterion maximizes long-term growth rate by determining
    the optimal fraction of capital to allocate to a trade based on
    the expected return and volatility.

    Args:
        signal_strength: Model confidence (0.0 to 1.0)
        portfolio_value: Total portfolio value in dollars
        risk_tolerance: Maximum risk per trade (0.0 to 1.0)
        volatility: Asset volatility (annualized standard deviation)

    Returns:
        Dictionary containing:
        - position_size: Dollar amount to invest
        - quantity: Number of shares
        - risk_amount: Total risk exposure
        - stop_loss_price: Recommended stop loss

    Raises:
        ValidationError: If parameters are out of valid range

    Example:
        >>> calculate_position_size(0.75, 100000, 0.02, 0.25)
        {'position_size': 1500.00, 'quantity': 10, ...}
    """
    pass
```

### Updating Documentation

When adding features, update:

1. **API.md** - Add new endpoints
2. **FEATURE_MATRIX.md** - Add feature entry
3. **USAGE.md** - Add usage examples
4. **CONFIGURATION.md** - Add config options
5. **examples/** - Create example files

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally (`pytest`)
- [ ] Code coverage meets requirements
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] Commit messages follow conventions

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No new warnings

## Related Issues

Closes #123
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer approval required
3. Address review feedback
4. Squash commits before merge (optional)

### CI/CD Pipeline

Automated checks on every PR:

```yaml
jobs:
  - Linting (flake8, black, mypy, eslint)
  - Unit tests
  - Integration tests
  - Code coverage report
  - Security scanning
  - Build Docker images
```

---

## Project Structure for Contributors

```text
backend/
├── <service_name>/
│   ├── __init__.py
│   ├── app.py           # Flask application
│   ├── <module>.py      # Business logic
│   └── README.md        # Service-specific docs
├── common/              # Shared utilities
└── config_files/        # Configuration

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── system/              # End-to-end tests
└── conftest.py          # Pytest fixtures

docs/                    # Documentation
└── examples/            # Code examples
```

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
