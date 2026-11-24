# Renderer toolkit

This folder contains the frame-capture renderer tools and reusable visual styles used by the Faceless Video Pipeline.

## Available renderer styles

- **Tall Tale**: flat 2D cartoon characters staged in a stylized 3D world. Used by the example English and Telugu channel profiles.
- **Cinematic What If**: English-only 2D ink-vector scenes with a locked cast and detailed per-shot art direction.

**Engineering Explainer** is a topic/art-direction profile implemented on the Tall Tale renderer. It is not a separate renderer. The styles/archive directory is reference material and is not enabled for new projects.

A style is runnable only if it has a style guide and a complete example project. The command bash scripts/new_video.sh --list reports styles that can be scaffolded through the generic capture pipeline.

## Requirements

- Node.js 22 or later
- Python 3.10 or later
- FFmpeg and ffprobe
- Chrome or Chromium for headless rendering
- Optional local voice and word-timing models; the setup helper downloads these model files

Some automated generation, media, analytics, and publishing integrations require separate provider accounts or credentials. Model usage may have a cost. YouTube Analytics access is read-only; publishing requires a separate write authorization.

## Create a project

    bash scripts/new_video.sh tall-tale my-video
    cd my-video
    node tools/capture.mjs check

Read the selected style's STYLE.md before editing its script or renderer. Keep the OP drawing and capture interfaces stable so frame extraction, contact sheets, video rendering, and audio tools continue to work.

See the repository README and daily/PRODUCTION_STANDARD.md for setup, operating instructions, reusable assets, audio QA, and release checks.
