#!/usr/bin/env python3
"""Legacy entry point; implementation lives in faceless_shorts.feedback.loop."""
from _entrypoint import expose

_app = expose("faceless_shorts.feedback.loop", globals())

if __name__ == "__main__":
    raise SystemExit(_app.main())
