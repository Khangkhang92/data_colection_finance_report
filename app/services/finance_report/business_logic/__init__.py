"""Finance API service package."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[4]
_COMMON_SERVICE_ROOT = _PROJECT_ROOT / "app" / "common"

if str(_COMMON_SERVICE_ROOT) not in sys.path:
    sys.path.append(str(_COMMON_SERVICE_ROOT))

__version__ = "0.1.0"
