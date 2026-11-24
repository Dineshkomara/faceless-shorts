#!/usr/bin/env bash
# Daily video pipeline runner. Safe to invoke from any working directory.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$HOME/.gemini/antigravity/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$DEFAULT_ROOT/.env" ]; then set -a; . "$DEFAULT_ROOT/.env"; set +a; fi
ROOT="${PIPELINE_ROOT:-$DEFAULT_ROOT}"
PROJECTS_DIR="${PIPELINE_PROJECTS_DIR:-$ROOT/projects}"
DIR="$ROOT/daily"
SKILL="${SKILL_DIR:-$ROOT/.agents/skills/faceless-shorts}"
if [ ! -d "$SKILL" ] && [ -d "$HOME/.config/opencode/skill/faceless-shorts" ]; then
  SKILL="$HOME/.config/opencode/skill/faceless-shorts"
fi
CLI="${OPENCODE_CLI:-}"
if [ -z "$CLI" ]; then CLI="$(command -v opencode-cli || command -v opencode || true)"; fi
if [ -z "$CLI" ] && [ -x "/Applications/OpenCode.app/Contents/Resources/opencode-cli" ]; then
  CLI="/Applications/OpenCode.app/Contents/Resources/opencode-cli"
fi
if [ -z "$CLI" ]; then echo "OpenCode CLI not found; set OPENCODE_CLI or install it." >&2; exit 127; fi
mkdir -p "$PROJECTS_DIR"
export SKILL SKILL_DIR="$SKILL" PIPELINE_ROOT="$ROOT" PIPELINE_PROJECTS_DIR="$PROJECTS_DIR" OPENCODE_CLI="$CLI"
EN_CHANNEL_NAME="${EN_CHANNEL_NAME:-Curiography}"
TE_CHANNEL_NAME="${TE_CHANNEL_NAME:-Asakthi}"
LOG="$DIR/logs/$(date +%F).log"
LOCK="$DIR/.run.lock"
mkdir -p "$DIR/logs"
touch "$DIR/topics-done.md"

# --- single instance guard -------------------------------------------------------------------
# A run takes 40-90 min; the 10:00 and 19:00 slots can overlap. Two agents at once means duplicate
# uploads and a fight over the same project dir, so a second runner refuses to start.
if [ -f "$LOCK" ]; then
  OLDPID=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
    {
      echo "===== $(date) : run start (DRY_RUN=${DRY_RUN:-0}) ====="
      echo "skipped: a previous run is still active (pid $OLDPID, an existing lock file)"
      echo "===== $(date) : run end, exit=0 ====="
    } >> "$LOG" 2>&1
    exit 0
  fi
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT INT TERM

# Channel filter: all | en | te (default all)
CHANNEL="${1:-${CHANNEL_FILTER:-all}}"
EXTRA_INSTRUCTION=""
if [ "$CHANNEL" = "en" ]; then
  EXTRA_INSTRUCTION="CHANNEL RESTRICTION: Execute ONLY the English channel ($EN_CHANNEL_NAME). Do NOT scaffold, script, or render the Telugu video in this run."
elif [ "$CHANNEL" = "te" ]; then
  EXTRA_INSTRUCTION="CHANNEL RESTRICTION: Execute ONLY the Telugu channel ($TE_CHANNEL_NAME, section 2b). Do NOT scaffold, script, or render the English video in this run. If $PROJECTS_DIR/daily-$(date +%Y%m%d)-te is already uploaded or is a translated non-mythological video, scaffold a fresh project: $PROJECTS_DIR/daily-$(date +%Y%m%d)b-te based strictly on python3 trend_hunter.py --channel te."
fi

if [ -n "$TOPIC_OVERRIDE" ]; then
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
TOPIC OVERRIDE: Focus this video strictly on this specific trending topic/hook: \"$TOPIC_OVERRIDE\"."
fi

STYLE_OVERRIDE="${STYLE_OVERRIDE:-auto}"
REQUESTED_STYLE="$STYLE_OVERRIDE"
if [ "$STYLE_OVERRIDE" = "auto" ]; then STYLE_OVERRIDE="tall-tale"; fi
STYLE_PROFILE=""
STYLE_DETAIL=""
STYLE_USAGE="STYLE STANDARD: Use the installed '$STYLE_OVERRIDE' renderer with the channel's established art direction."
if [ "$REQUESTED_STYLE" = "engineering-explainer" ]; then
  STYLE_OVERRIDE="tall-tale"
  STYLE_PROFILE=$(cat "$DIR/REFERENCE_ENGINEERING.md")
  STYLE_USAGE="STYLE PROFILE: Engineering Explainer uses the installed Tall Tale 3D renderer scaffold and follows the engineering visual/story profile below."
elif [ "$REQUESTED_STYLE" = "cinematic-what-if" ]; then
  if [ "$CHANNEL" = "te" ]; then
    STYLE_OVERRIDE="tall-tale"
    STYLE_USAGE="STYLE NOTE: Cinematic What If is English-only. Keep this Telugu run on the established Asakthi/Tall Tale style."
  else
    STYLE_PROFILE=$(cat "$DIR/STYLE_CINEMATIC_WHAT_IF.md")
    STYLE_DETAIL=$(cat "$DIR/REFERENCE_CINEMATIC_WHAT_IF.md")
    STYLE_USAGE="STYLE OVERRIDE: Use the installed native 2D Canvas cinematic-what-if renderer; never render visible 3D assets or run 3D-only character/background setup. This style's visual and story rules supersede generic English 3D instructions. Shared evidence, safety, audio, asset, and strict QA rules remain binding."
  fi
fi
if [ ! -f "$SKILL/styles/$STYLE_OVERRIDE/example/index.html" ] || [ ! -f "$SKILL/styles/$STYLE_OVERRIDE/example/src/main.js" ] || [ ! -f "$SKILL/styles/$STYLE_OVERRIDE/example/tools/capture.mjs" ]; then
  echo "Style '$REQUESTED_STYLE' has no installed runnable example. Available renderer styles: $(bash "$SKILL/scripts/new_video.sh" --list | tr '\n' ' ')" >&2
  exit 2
fi
QUALITY_STANDARD=$(cat "$DIR/PRODUCTION_STANDARD.md")
PRIVATE_CONTEXT=""
if [ -f "$DIR/private.local.md" ]; then PRIVATE_CONTEXT=$(cat "$DIR/private.local.md"); fi
EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
${PRIVATE_CONTEXT}
PROJECT STORAGE: Create and update video project directories only inside $PROJECTS_DIR. Keep source code and daily pipeline records in the repository's existing directories.
SHARED PRODUCTION QUALITY STANDARD (MANDATORY FOR BOTH ENGLISH AND TELUGU; supersedes conflicting older camera, shot-count, dialogue, and audio instructions):
${QUALITY_STANDARD}

${STYLE_USAGE}

${STYLE_PROFILE}

${STYLE_DETAIL}

INDEPENDENT CHANNELS & CONCEPT SEPARATION (MANDATORY):
1. English Channel ($EN_CHANNEL_NAME): Make concise, retellable explainers across human instincts/cognitive biases, everyday psychology, body/brain, animal behavior, physical science, history with a strong mechanism, and engineering. Favor a concrete situation and a surprising, sourceable mechanism that can be shown as one clean visual story. Engineering is one topic lane, not the whole channel. Scout with python3 trend_hunter.py --channel en --count 8, then verify key claims using at least two credible sources. Never present a made-up illustrative story as a true event.
2. Telugu Channel ($TE_CHANNEL_NAME): MUST BE 100% INDEPENDENT AT CONCEPT LEVEL. Strictly focused on Hindu Mythology (Ramayana, Mahabharata, Bhagavatam, Puranas), Telugu story books (Chandamama kathalu, Vikram-Betal, Tenali Ramakrishna, Maryada Ramanna, Panchatantra), or sacred Telugu temple mysteries. Scouted via: python3 trend_hunter.py --channel te.
CRITICAL: NEVER translate, dub, or adapt the English video for Telugu! Both channels must have completely distinct stories, characters, and scripts from the concept level up.

AUTOMATED 8-CRAFT CINEMA PIPELINE (MANDATORY FOR ALL RUNS):
Every video must automatically execute the 8 Filmmaking Crafts across its lifecycle without separate toggles:
1. CRAFT: SCREENWRITER — For English, build one concise concept-led story around a real, sourceable mechanism; for Telugu folklore, follow the source story. Use dialogue only when the source story genuinely contains speaking characters. Declare only actual speakers in script.json.
2. CRAFT: CASTING & VOICE — Use one stable native-language narrator for explainers (Edge-TTS neural for English, configured Telugu narrator); reserve distinct dialogue voices for stories with genuine dialogue.
3. CRAFT: CHARACTER DESIGNER — Use character-design tools only when the story needs visible characters (most English concepts need no cast); Telugu myth and folklore still use custom designs and audit sheets.
4. CRAFT: PRODUCTION DESIGNER — Execute setup_backgrounds.py to establish atmospheric 9:16 and panoramic sets with cinematic lighting.
5. CRAFT: CINEMATOGRAPHER & DIRECTOR — Choreograph purposeful camera movement, clean 3-point lighting, and distinct shot scales in src/shots.js; movement must support the idea and hold still when clarity benefits.
6. CRAFT: SOUND DESIGNER — Match music and effects to the scene and channel: English concepts use a restrained curious score and selective effect cues; English engineering uses scene-matched engineering foley; Telugu stories use folklore ambience and foley. Keep narration clear and duck music smoothly via mix.py. Avoid generic room tone, irrelevant footsteps/armor, and a cue on every cut.
7. CRAFT: FILM EDITOR & VFX — Enforce pacing gates (no dead air >0.5s), J/L-cuts, word-by-word highlight subtitles (emerald green box for Telugu), and visual contact sheet validation (review/all.jpg).
8. CRAFT: PACKAGING & PUBLISHING — Generate custom high-CTR cover and upload to YouTube with pinned engagement comment seed."

if [ "$PRODUCTION_FORMAT" = "episode" ]; then
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
PRODUCTION FORMAT: Cinema Episodic Mode (3-5 minutes). Structure the script with 3 dramatic scene acts."
fi

if [ "$REQUESTED_STYLE" = "cinematic-what-if" ]; then
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
FINAL STYLE APPLICATION: Cinematic What If is an English-only native 2D Canvas renderer. Apply it only to the English episode. Ignore conflicting generic 3D craft/setup steps for that episode; implement set and character design in the 2D renderer. Keep Telugu on its own selected style."
fi

# --- PHASE 1: INSTANT BROADCAST OF PRE-RENDERED QUEUED VIDEOS ----------------
{
  echo "===== $(date) : [PHASE 1] INSTANT BROADCAST CHECK (CHANNEL=$CHANNEL) ====="
  python3 "$DIR/broadcast_queue.py" broadcast --channel "$CHANNEL" || echo "  (Queue empty or pre-production cold start; continuing to generate)"
} >> "$LOG" 2>&1

# Refresh audience metrics after the broadcast attempt; authorization is optional until configured.
YT_TOKEN_DIR="${YT_ANALYTICS_TOKEN_DIR:-$HOME/.config/faceless-shorts}"
if [ -f "$YT_TOKEN_DIR/youtube-analytics-en-token.json" ] || [ -f "$YT_TOKEN_DIR/youtube-analytics-te-token.json" ]; then
  {
    echo "===== $(date) : [ANALYTICS] Refreshing YouTube performance data ====="
    python3 "$DIR/youtube_analytics.py" sync || echo "Analytics refresh skipped or unavailable; video production continues."
  } >> "$LOG" 2>&1
fi

# --- PHASE 2: PRE-PRODUCTION FOR NEXT SCHEDULED BROADCAST SLOT ---------------
NEXT_SLOT=$(python3 "$DIR/broadcast_queue.py" next-slot 2>/dev/null || echo "upcoming slot")

# If MPT engine is selected, bypass LLM prompt generation and run mpt_pipeline directly
if [ "$ENGINE_MODE" = "mpt" ]; then
  {
    echo "===== $(date) : [ENGINE: MoneyPrinterTurbo] Starting MPT production for CHANNEL=$CHANNEL (DRY_RUN=${DRY_RUN:-0}) ====="
    MPT_ARGS=(--channel "$CHANNEL")
    [ -n "$TOPIC_OVERRIDE" ] && MPT_ARGS+=(--topic "$TOPIC_OVERRIDE")
    [ "$DRY_RUN" = "1" ] && MPT_ARGS+=(--dry-run)
    python3 "$DIR/mpt_pipeline.py" "${MPT_ARGS[@]}"
    STATUS=$?
    echo "===== $(date) : run end, exit=$STATUS ====="
  } >> "$LOG" 2>&1
  exit $STATUS
fi

EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
BROADCAST PIPELINE: PRODUCE AHEAD FOR NEXT SLOT ($NEXT_SLOT)
You are producing and rendering the master video for the upcoming $NEXT_SLOT broadcast slot.
Once the video is rendered, cover generated, and QA contact sheets verified, stage it in renders/ and covers/ ready for the next scheduled broadcast trigger."

if [ "$CHANNEL" != "te" ]; then
  CONCEPT_PROFILE=$(cat "$DIR/REFERENCE_CONCEPT.md")
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
ENGLISH CONCEPT-EXPLAINER PROFILE (applies only to Curiography; keep Asakthi independent):
${CONCEPT_PROFILE}"
  if [ "$TOPIC_LANE" = "engineering" ] && [ "$REQUESTED_STYLE" != "engineering-explainer" ] && [ "$REQUESTED_STYLE" != "cinematic-what-if" ]; then
    REFERENCE_PROFILE=$(cat "$DIR/REFERENCE_ENGINEERING.md")
    EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
OPTIONAL ENGINEERING TOPIC LANE (use only because TOPIC_LANE=engineering):
${REFERENCE_PROFILE}"
  fi
  FEEDBACK_GUIDANCE=$(python3 "$DIR/feedback_loop.py" guidance --channel en 2>/dev/null || echo "No saved review history yet; apply the strict quality gate below.")
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
PRIOR VIDEO FEEDBACK: Use this history to improve exactly one weak point in the next English video:
${FEEDBACK_GUIDANCE}"
else
  FEEDBACK_GUIDANCE=$(python3 "$DIR/feedback_loop.py" guidance --channel te 2>/dev/null || echo "No saved review history yet; apply the strict quality gate below.")
  EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
PRIOR VIDEO FEEDBACK: Use this history to improve exactly one weak point in the next Telugu video:
${FEEDBACK_GUIDANCE}"
fi
EXTRA_INSTRUCTION="${EXTRA_INSTRUCTION}
ASSET LIBRARY (both channels): After choosing a topic but before coding, search with python3 \"$DIR/asset_library.py\" search \"<topic> <needed props or environments>\". Reuse a relevant modular asset if it fits the current story and preserves a clean frame; otherwise build a new one. Record search queries, reused IDs, and newly archived asset IDs in review/quality_review.json. Do not copy old HUD clutter, compositions, or language-specific material across channels."

# --- model selection -------------------------------------------------------------------------
# Probe after Phase 1 so quota checks never delay a queued video upload. The first responsive
# model is primary; retained candidates provide cross-provider fallbacks for generation errors.
PICKED=$(python3 "$DIR/pick_model.py" --refresh 2>/dev/null)
if [ -z "$PICKED" ]; then
  {
    echo "===== $(date) : run blocked before generation: no model passed the availability probe ====="
    echo "Check model/provider quota or availability, then retry from the dashboard."
    echo "===== $(date) : run end, exit=1 ====="
  } >> "$LOG" 2>&1
  exit 1
fi
REST=$(python3 "$DIR/pick_model.py" --list 2>/dev/null | grep -v "^${PICKED}$")
MODELS=("$PICKED")
while IFS= read -r m; do [ -n "$m" ] && MODELS+=("$m"); done <<< "$REST"

{
  echo "===== $(date) : run start (DRY_RUN=${DRY_RUN:-0}, CHANNEL=$CHANNEL, NEXT_SLOT=$NEXT_SLOT) model=$PICKED ====="
  cd "$DIR"
  STATUS=1
  ATTEMPT=0
  ATTEMPT_COUNT=${#MODELS[@]}
  for M in "${MODELS[@]}"; do
    ATTEMPT=$((ATTEMPT + 1))
    TMP=$(mktemp)
    echo "===== $(date) : model attempt $ATTEMPT/$ATTEMPT_COUNT: $M ====="
    "$CLI" run --auto --agent build --model "$M" "$(cat "$DIR/PROMPT.md")

EXTRA RULES: Today is $(date +%F). If DRY_RUN=1 is set in your environment, obey the DRY-RUN rule in the prompt.
$EXTRA_INSTRUCTION" 2>&1 | tee "$TMP"
    STATUS=${PIPESTATUS[0]}
    # Do not replay a whole production after YouTube has already halted an upload.
    if grep -qE "🛑 \[UPLOAD HALTED\]|🛑 \[API THROTTLED\]" "$TMP"; then
      echo "⚠️ [PIPELINE HALT] YouTube/Zapier API is rate-limited/throttled. Halting run immediately without model retries."
      rm -f "$TMP"
      STATUS=0
      break
    fi
    # Check for LLM model quota / rate limit failures first so we can fall back to next model
    if [ "$STATUS" -ne 0 ] && grep -qiE "unavailable|high demand|currently experiencing|overloaded|credit_balance|usage limit|rate limit|quota|429|503|500|exhausted|failed to fetch|no longer available|limit reached|retry in|exceeded your current quota" "$TMP"; then
      echo "(model $M unavailable, retired, or quota reached — trying next model in catalog)"
      rm -f "$TMP"
      continue
    fi
    rm -f "$TMP"
    break
  done
  echo "===== $(date) : run end, exit=$STATUS ====="
} >> "$LOG" 2>&1
exit $STATUS
