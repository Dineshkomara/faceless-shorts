# Contributing

- Keep generated episodes, credentials, local run logs, and personal channel history out of commits.
- Keep each renderer style self-contained under `styles/<style>/`, with a complete `example/`, `STYLE.md`, asset licenses, and a stable `OP.draw` / `OP.frame` capture API.
- Update `daily/PRODUCTION_STANDARD.md` and the dashboard only when the runtime behavior changes; avoid rules that contradict a selected style's guide.
- Use repo-relative paths or documented environment overrides. Never add a machine-specific absolute home path.
- Keep network publishing and account integrations opt-in; do not enable upload as part of setup.
