# Automated video production run

You are running unattended. Do not ask questions or wait for approval. Use the environment and channel filter supplied by run-daily.sh. This file is the operating procedure; the selected style guide and PRODUCTION_STANDARD.md define detailed production and quality rules.

## 1. Protect existing work

- Work only inside the repository root supplied in PIPELINE_ROOT; the current run folder is daily/.
- Read daily/topics-done.md and inspect the queue before starting a new concept. Do not repeat a topic or overwrite an existing project. Resume a valid unfinished project when possible.
- Never write credentials, account IDs, or OAuth data into source files. If daily/private.local.md is injected, use it only to select the correct user-authorized upload connection.
- DRY_RUN=1 means create and review a candidate but do not upload or stage it for automatic broadcast.

## 2. Choose a topic and style

Follow the selected channel's editorial profile below. A topic must be original, sourceable, visually explainable, and clearly distinct from the other channel's concept.

- **English example profile:** human instincts, cognitive bias, everyday psychology, the body and brain, animals, physical science, history, and engineering. Favor an everyday situation with a counterintuitive mechanism and a concise payoff. Do not restrict the channel to engineering.
- **Telugu example profile:** independent Telugu folklore, epics, mythology, or temple traditions. Preserve the source story and cultural context. Never translate or adapt the English episode.

Scout with python3 daily/trend_hunter.py --channel en --count 8 or --channel te. For English, STYLE_OVERRIDE=cinematic-what-if selects the dedicated human-centered 2D style; engineering-explainer uses the engineering art direction on the installed Tall Tale renderer; auto uses the channel's default renderer. Telugu stays on its own established style. Only select renderer styles listed by bash $SKILL/scripts/new_video.sh --list.

Verify every important claim against at least two reliable sources and store direct source URLs in script.json. Clearly label hypothetical or illustrative scenes. Avoid unsupported exact numbers, invented anecdotes presented as true, medical advice, gore, and claims that exceed the evidence.

## 3. Plan the episode before code

Read:

- daily/PRODUCTION_STANDARD.md
- The selected style's STYLE.md
- For cinematic-what-if, also read daily/REFERENCE_CINEMATIC_WHAT_IF.md
- For the engineering profile, read daily/REFERENCE_ENGINEERING.md
- For the English default concept profile, read daily/REFERENCE_CONCEPT.md

Write review/production_board.md before changing renderer code. The board must have one self-contained production card for every stable shot ID in src/shots.js, plus the title, premise, evidence map, full character and set references, timing, camera, action, lighting, sound, continuity, safe areas, negative directions, and asset-library decisions required by the production standard.

Search the reusable asset library before creating props or scene utilities:

    python3 PIPELINE_ROOT/daily/asset_library.py search "<topic and needed assets>"

Reuse suitable clean assets; archive only useful modular assets after review. Record the search and any reuse in review/quality_review.json.

## 4. Build and review

Create a project with the selected runnable style using new_video.sh; write script.json, the production board, and episode-specific src/shots.js. Preserve the renderer's OP.draw and OP.frame APIs. Use the project's timing, voice, caption, and mixer tools. Each cue must map to a real implemented sound. Keep speech natural and clear over restrained music, use selective scene-matched effects, and check the complete mix.

Run the renderer check, cue extraction, sound mix, contact sheet, and final render using commands documented by the selected style. Review the contact sheet and full-size frames from the opening, every major set, the busiest caption/graphic, and the payoff. Fix repeated shots, noisy frames, collisions, unclear actions, timing problems, factual errors, and audio defects before staging.

Complete review/quality_review.json with honest evidence, scores, checks, asset-library records, and one next improvement. Run:

    python3 PIPELINE_ROOT/daily/feedback_loop.py record-qa --project "$PWD" --channel <en|te>

A failed strict gate means fix and review again. Never fabricate a listening check, source check, render, or visual inspection to pass the gate.

## 5. Stage and publish

Only stage a rendered episode after it passes the feedback gate, has its matching cover, and has been reviewed. When not in dry-run, follow the queue's configured schedule and upload only through the correct account connection from daily/private.local.md. If the connection is missing or unclear, leave the video staged and report that publishing needs configuration. Never expose, print, or commit connection identifiers. Update the local topic ledger with the actual project status and useful feedback.

## 6. Run summary

Report the chosen topic and sources, selected style, project path, render and QA status, upload/queue status, any remaining issue, and the next concrete improvement. Do not claim steps that were not completed.
