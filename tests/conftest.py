"""Shared pytest setup for the OdorSig test suite."""
import os
import sys
import tempfile

# code/Automation_code/config.py creates its runtime directories on import.
# Point them at a throwaway temp dir so importing config during tests never
# writes into the working tree.
os.environ.setdefault("ODORSIG_BASE_DIR", tempfile.mkdtemp(prefix="odorsig_test_"))

# Make `code/` importable so tests can do `from Automation_code... import ...`,
# exactly as the app does when run from the code/ directory.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "code"))
