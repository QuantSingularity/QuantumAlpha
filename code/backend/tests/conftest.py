"""
Backend test conftest - ensures packages are importable from the code/ root.
"""

import os
import sys

# code/ root is two levels up from backend/tests/
code_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if code_root not in sys.path:
    sys.path.insert(0, code_root)

# backend/ directory is one level up from backend/tests/
# This allows bare imports like `from risk_service.x` and `from execution_service.x`
# which the integration tests use (without the `backend.` prefix).
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)
