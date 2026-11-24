---
name: faceless-shorts
description: A local toolkit for creating narrated, captioned, procedurally animated short videos with selectable visual styles, frame capture, audio mixing, and YouTube integrations.
---

# Faceless Shorts Renderer Toolkit

This folder is the repository's reusable renderer bundle. The dashboard and daily runner set SKILL_DIR to this location. Projects are created under PIPELINE_ROOT unless an explicit --dir is supplied.

## Runnable styles

A style is runnable through new_video.sh only when it has STYLE.md and a complete example project with index.html, src/main.js, and tools/capture.mjs.

- tall-tale: 2D cartoon characters inside a stylized 3D environment; configured for the existing story/folklore channel.
- cinematic-what-if: English-only low-key 2D ink-vector visuals, locked character designs, cinematic flat-vector environments, and restrained atmosphere.

engineering-explainer is an editorial/art-direction profile that uses the Tall Tale renderer scaffold. It is not a separate renderer. The styles/archive folder contains references that are not enabled by the runner. Do not select an archived style until it has a complete scaffold and is listed by new_video.sh --list.

## Renderer contract

Each project keeps its style's renderer contract:

- OP.draw(time) draws the requested frame.
- OP.frame(time, quality) returns the captured frame image.
- OP.duration(), OP.shots(), OP.captions(), and OP.cues() expose timeline information to the capture and review tools.

Keep frames deterministic at a given time. Keep audio, narration, caption timing, capture, and cover tools intact when adding a style. Read the chosen STYLE.md and the shared daily/PRODUCTION_STANDARD.md before changing a project.

## Common commands

    bash scripts/new_video.sh --list
    bash scripts/new_video.sh tall-tale example
    node tools/capture.mjs check
    node tools/capture.mjs cues
    python3 tools/mix.py .
    node tools/capture.mjs sheet review/all.jpg 1 8
    node tools/capture.mjs video renders/video.mp4

The local setup helper can install Python voice/timing dependencies and download model files; see scripts/setup.sh before running it. Model-provider use, stock-media services, analytics, and publishing may require separate accounts, credentials, or paid plans. Setup never uploads to YouTube.

## Safe publishing

YouTube Analytics uses the read-only scope. Uploading is a separate write integration. Keep credentials outside the repository, use daily/private.local.md for local channel routing details, and do not upload unless the pipeline is configured to use the correct channel connection.
