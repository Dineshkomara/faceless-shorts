# Faceless-shorts reusable asset library

This is a cross-project library for modular props, environments, visual utilities, sound palettes, and strong scene references. Search it before building a new 3D set. Reuse only the parts that clarify the current idea and pass the phone-size visual-cleanliness gate.

## Rules

- Preserve the original project and source paths in each bundle. `index.json` stores tags, provenance, descriptions, and SHA-256 checksums.
- `python3 daily/asset_library.py search "topic props environment"` finds candidate bundles.
- `python3 daily/asset_library.py use --id <id> --project <project-path>` copies compatible files into a project. It never overwrites differing project files; conflicts must be reviewed and adapted manually.
- After a project passes QA, archive only modular, useful assets with `asset_library.py archive`. Include dependencies, meaningful tags, and concise integration notes. Do not archive entire projects as reusable assets.
- Record IDs reused or archived in the project's `review/quality_review.json` and `.asset-library.json`.
- Keep reference-only content clearly labeled. Do not carry over UI clutter, composition flaws, copyrighted third-party imagery/audio, or factual claims from a reference asset.

The first bundle is a reusable driving/road prop kit from the target-fixation short. Its vehicle, roadway, tree, and cockpit geometry may be useful for future attention, driving, or hazard concepts. Its crowded banners, caption treatment, and repeated framing are explicitly excluded from reuse.
