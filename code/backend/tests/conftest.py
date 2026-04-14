"""
Backend test conftest - ensures packages are importable from the code/ root.
"""

import os
import sys

# code/ root is two levels up from backend/tests/
code_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if code_root not in sys.path:
    sys.path.insert(0, code_root)
