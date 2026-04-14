"""
Root conftest.py - adds the code/ directory to sys.path so that
`backend` and `ai_models` packages are importable during test runs.
"""

import os
import sys

# Insert the code/ directory so `backend` and `ai_models` are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
