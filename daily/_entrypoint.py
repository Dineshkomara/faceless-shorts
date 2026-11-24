"""Compatibility bridge for historical daily/ command paths."""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))


def expose(module_name, namespace):
    """Expose a packaged command's public names under its old import path."""
    module = importlib.import_module(module_name)
    namespace.update({key: value for key, value in vars(module).items() if not key.startswith("__")})
    return module
