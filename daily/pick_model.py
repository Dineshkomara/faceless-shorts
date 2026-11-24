#!/usr/bin/env python3
"""Legacy entry point; implementation lives in faceless_shorts.models.selector."""
from _entrypoint import expose

_app = expose("faceless_shorts.models.selector", globals())

if __name__ == "__main__":
    raise SystemExit(_app.main())
