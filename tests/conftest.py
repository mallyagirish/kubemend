"""Make the engine and both apps importable without an install step."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for entry in ("engine", "apps/kubemend-cli", "apps/kubemend-report"):
    path = os.path.join(ROOT, entry)
    if path not in sys.path:
        sys.path.insert(0, path)
