"""Make src/notebooks importable (jobs_api, waves_manifest, app_probes) for the unit tests.

Run from the bundle root: pytest tests
Inside a workspace folder (no __pycache__ allowed there):
    PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider --assert=plain tests
"""

import os
import sys

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BUNDLE_ROOT, "src", "notebooks"))
