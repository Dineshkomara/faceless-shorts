# Faceless Video Pipeline

A local-first toolkit for researching, scripting, rendering, reviewing, and optionally publishing narrated faceless videos. It includes an OpenCode-driven production runner, a browser dashboard, a reusable asset library, strict pre-publish QA, YouTube Analytics import, and selectable renderer styles.

This repository contains a packaged pipeline core and reusable style scaffolds. Scheduling is opt-in; the setup helper does not install a background service. It does **not** contain generated episodes, channel history, OAuth tokens, model caches, or rendered media.

## What is included

- `src/faceless_shorts/`: application package grouped by analytics, assets, feedback, models, publishing, topics, renderer engines, and web dashboard.
- `daily/`: production guidance and backward-compatible CLI/runner paths.
- `dashboard/`: backward-compatible dashboard launcher and local performance data.
- `.agents/skills/faceless-shorts/`: renderer tools and reusable style scaffolds.
- `asset-library/`: documentation for reusable props and utilities; each operator maintains their own local index.
- `docs/`: architecture, scheduling, and Analytics setup guides.

Included working visual styles are `tall-tale` and `cinematic-what-if`. The latter is an optional English-only 2D Canvas style. Archived style references are retained for study and are not promised as runnable scaffolds.

## Requirements

- macOS or Linux with Python 3.10+, Bash, and FFmpeg.
- OpenCode CLI and a configured model provider for automated script/production generation.
- Google Chrome or Chromium for headless frame capture.
- A user-authorized Zapier YouTube connection only if you enable uploads.
- YouTube Analytics OAuth client only if you enable analytics import.

Some optional voice/render tools have their own dependencies; see `.agents/skills/faceless-shorts/README.md` and each style's `STYLE.md`.

## Quick setup

1. Clone this repository and open a shell in its root.
2. Copy `.env.example` to `.env` and set optional paths. The repository is the pipeline root; generated video projects go under `projects/` by default. Set `PIPELINE_PROJECTS_DIR` to choose another output location.
3. Run `python3 -m pip install -e .` to install the package and its command-line entry points. Then run `./setup.sh` to check local prerequisites. Install FFmpeg, OpenCode CLI, and a supported browser as needed. Configure OpenCode with at least one model provider.
4. Review `daily/PROMPT.md`, `daily/REFERENCE_CONCEPT.md`, and `daily/PRODUCTION_STANDARD.md`. Customize the channel/topic rules and voice settings for your own audience before generating anything.
5. Run `faceless-topics --help` to explore topic research. Start the local dashboard with `./start-dashboard.sh` and visit `http://127.0.0.1:8788/`.
6. Use `DRY_RUN=1` when trying the production runner for the first time. For recurring runs, follow [the scheduling guide](docs/operations/scheduling.md); scheduled publishing should remain disabled until you configure and verify your own account connection.

Do not put OAuth JSON files, refresh tokens, `.env`, or provider credentials in the repository. The analytics helper stores tokens outside the repository with owner-only file permissions.

For Zapier uploads, configure YOUTUBE_CONNECTION_EN and YOUTUBE_CONNECTION_TE in the ignored `.env` file. The uploader refuses to publish when the selected channel has no explicit connection configured; it will not guess from a default account. Zapier requires a fetchable URL, so enabling ALLOW_PUBLIC_FILE_HOSTING=1 transfers the video and cover to a public third-party file host first. Do not enable that setting for private media.

## Run commands

```bash
# Research English topics
faceless-topics --channel en --count 8

# Research Telugu topics
faceless-topics --channel te --count 8

# Start dashboard
./start-dashboard.sh

# Read-only YouTube Analytics setup and sync
faceless-analytics authorize --profile en
faceless-analytics sync --profile en

# Scheduled pipeline entry point (configure your channel rules first)
DRY_RUN=1 bash daily/run-daily.sh en
```

The dashboard binds to loopback by default. Keep it local unless you add authentication and a secure remote deployment model.

For read-only channel analytics setup, see [the YouTube Analytics guide](docs/operations/youtube-analytics.md).

## Configuration and personalization

Set optional EN_CHANNEL_NAME and TE_CHANNEL_NAME in `.env` for dashboard labels. A fork should also change channel topics, language, voice, schedule, and upload rules in `daily/PROMPT.md`, `daily/REFERENCE_CONCEPT.md`, and `daily/run-daily.sh`; internal channel keys stay `en` and `te`. Keep channel-specific credentials in local config; do not hardcode secrets.

For a new style, create `.agents/skills/faceless-shorts/styles/<style>/STYLE.md` and a complete `example/` project. Each renderer must keep the `OP.draw` and `OP.frame` capture interface. See the installed style guides and `daily/PRODUCTION_STANDARD.md` for production-board and QA requirements. See [the architecture guide](docs/architecture.md) for package boundaries and compatibility entry points.

## Data and publishing behavior

The pipeline can stage videos for later publishing. Review queue settings and the publishing code before enabling unattended upload. YouTube Analytics access is read-only; uploads use a separate, explicitly configured Zapier YouTube connection. Disable or remove those integrations if you only want local rendering.

## Repository safety

`.gitignore` excludes credentials, run logs, model caches, user-installed skills, generated video projects, and large media output. Review `git status --ignored` and `git diff --check` before pushing. Never force-add ignored secrets or generated private channel history.

## License

MIT. Third-party fonts and bundled libraries retain their own licenses, which are included alongside the assets where applicable.
