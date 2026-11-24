# Architecture

The repository separates reusable application code from operational adapters and local runtime data.

```text
src/faceless_shorts/       Python application package, grouped by capability
  analytics/               Read-only YouTube Analytics integration
  assets/                  Reusable asset registry
  engines/                 Renderer-engine adapters
  feedback/                Quality gate and learning-loop records
  models/                  Model availability and fallback selection
  publishing/              Queue selection and scheduled publishing
  topics/                  Topic discovery and research
  web/                     Local dashboard server and HTML template
daily/                     Operational prompt/configuration and compatible CLI paths
dashboard/                 Dashboard launch shim and local performance data
projects/                  Local generated video projects (default; ignored by Git)
asset-library/             Reusable asset index and user-owned asset files
.agents/skills/             Renderer integration and complete style scaffolds
docs/                      Architecture and operator documentation
```

## Dependency direction

- `config.py` is the single source for repository-relative paths and local environment loading.
- Capability modules own their domain logic and use the shared path configuration.
- The web application and command-line entry points call capability modules; domain modules do not import the web layer.
- The `daily/*.py` and `dashboard/server.py` files are compatibility adapters. They preserve existing LaunchAgent, shell, dashboard, and OpenCode skill commands while the implementation lives under `src/`.
- Renderer styles remain self-contained plug-ins. The application selects and invokes them through the stable renderer contract rather than importing style internals.

## Runtime data

Secrets, generated episodes, model caches, logs, analytics metrics, and feedback records remain local and are excluded from Git. Generated episode projects are stored in `projects/` by default; `PIPELINE_PROJECTS_DIR` can point to a different output folder. `PIPELINE_ROOT`, `SKILL_DIR`, `MPT_STORAGE`, and related environment settings customize other locations without changing application code.

## Extending the system

Add a capability module under the matching package directory and expose a small CLI entry point only when operators need one. Keep provider and renderer integrations behind narrow adapters. Add shared paths or environment handling to `config.py`; avoid deriving repository locations independently in feature modules. Keep dashboard presentation in its template and HTTP behavior in the web package.
