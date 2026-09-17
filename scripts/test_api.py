"""
scripts/test_api.py
===================
Automated test runner for FastAPI backend endpoints.
Executes the comprehensive API test suite.
"""

import os
import sys

# Ensure root workspace is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from test_api import run_tests

if __name__ == "__main__":
    run_tests()
