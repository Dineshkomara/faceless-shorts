# Contributing

- Keep generated episodes, credentials, local run logs, and personal channel history out of commits.
- Put reusable Python application code under `src/faceless_shorts/`, grouped by capability. Keep HTTP presentation in `web/templates/` and local command adapters thin.
- Keep public CLI and launch paths backward-compatible. If an implementation moves, retain or update its compatibility entry point and document the supported command.
- Centralize repository and runtime paths in `faceless_shorts.config`; do not add independent home-directory or repository-root discovery in feature modules.
- Keep each renderer style self-contained under `.agents/skills/faceless-shorts/styles/<style>/`, with a complete `example/`, `STYLE.md`, asset licenses, and a stable `OP.draw` / `OP.frame` capture API.
- Update `daily/PRODUCTION_STANDARD.md`, the architecture guide, and operator documentation when runtime behavior or package boundaries change; avoid rules that contradict a selected style's guide.
- Use repo-relative paths or documented environment overrides. Never add a machine-specific absolute home path.
- Keep network publishing and account integrations opt-in; do not enable upload as part of setup.
