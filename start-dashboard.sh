#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
export PIPELINE_ROOT="${PIPELINE_ROOT:-$ROOT}"
export SKILL_DIR="${SKILL_DIR:-$PIPELINE_ROOT/.agents/skills/faceless-shorts}"
export PYTHONPATH="$PIPELINE_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m faceless_shorts.web.server "$@"
