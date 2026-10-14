import os
import sys

code_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if code_root not in sys.path:
    sys.path.insert(0, code_root)

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)
