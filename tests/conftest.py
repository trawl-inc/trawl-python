import sys
from pathlib import Path

# Lets the tests import samples.py as a plain module.
sys.path.insert(0, str(Path(__file__).parent))
