#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
printf 'Repository: %s\n' "$ROOT"
for tool in python3 node ffmpeg ffprobe; do
  if command -v "$tool" >/dev/null 2>&1; then printf '  %-8s %s\n' "$tool" "$(command -v "$tool")";
  else printf '  %-8s MISSING\n' "$tool"; fi
done
if command -v opencode-cli >/dev/null 2>&1; then printf '  %-8s %s\n' 'opencode' "$(command -v opencode-cli)";
elif command -v opencode >/dev/null 2>&1; then printf '  %-8s %s\n' 'opencode' "$(command -v opencode)";
else printf '  %-8s optional for automated generation (install and configure a provider)\n' 'opencode'; fi
printf '\nNext: copy .env.example to .env, customize daily/PROMPT.md, then run ./start-dashboard.sh.\n'
printf 'For local voice models, see .agents/skills/faceless-shorts/scripts/setup.sh; it downloads model files.\n'
