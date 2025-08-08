import os
import sys

# Ensure repo root is on sys.path for imports like 'services.*'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
