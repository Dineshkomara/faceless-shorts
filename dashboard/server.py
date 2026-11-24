#!/usr/bin/env python3
"""Compatibility entry point for existing dashboard launch services."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from faceless_shorts.web.server import main


if __name__ == "__main__":
    main()
