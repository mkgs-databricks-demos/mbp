# Rename: genie-ontology-sdk -> genie-ontology-modeled-knowledge-sdk

Date: 2026-11-25 | Branch: `mg-genie-ontology-modeled-knowledge-sdk`

## Decision (owner)
Before merging build-0, rename the project everywhere:

| Was | Now |
|---|---|
| folder `genie-ontology-sdk/`, pip name `genie-ontology-sdk` | `genie-ontology-modeled-knowledge-sdk/`, `genie-ontology-modeled-knowledge-sdk` |
| Python package `genie_ontology_sdk` (and vendored `genie_ontology_sdk_vendored`) | `genie_ontology_modeled_knowledge_sdk` (`genie_ontology_modeled_knowledge_sdk_vendored`) |
| title "Genie Ontology SDK" | "Genie Ontology Modeled Knowledge SDK" |

No backward-compatible import alias. History is left as written: the build-0 session summaries in this folder and `docs/reviews/2026-11-25_build-0-sdk-review.md` keep the old names, paths and ids because they record what ran.

## Changes
* `git mv` of every tracked file into `genie-ontology-modeled-knowledge-sdk/`; package, vendored folders (example and template), `docs/design/L100-genie-ontology-modeled-knowledge-sdk.md` and `docs/pitch/genie-ontology-modeled-knowledge-sdk-overview.html` renamed.
* The three names replaced in 112 files (code, tests, skills, templates, run kit, example project, plans, design docs, diagrams), plus the mbp root README row.
* The four example `ontology-metric-views/notebooks/*.ipynb` are workspace notebooks, so saving them added Databricks cell metadata; their code is identical to the template notebooks.
* Gitignored files moved with their folders (the example bundles' `variable-overrides.json`, `.rendered/`).

## Not changed
* The genie-build-waves instance (job names, `build_root`, `manifest_path`, the vars file outside the repo) still points at the old folder. Owner decision: update it at build 1.
* The Genie Code start-session notebook stays in the old `genie-ontology-sdk/` folder (it is tracked and in use), together with the ephemeral `.build-status/`.

## Verification
* No old name outside the history files (grep).
* pytest from a `/tmp` copy: 280 passed (run-kit test with genie-build-waves); vendored copies identical to `src/`.

## Files modified
* every tracked file of the project (moved), 112 with content changes
* this summary, `docs/sessions/INDEX.md`
