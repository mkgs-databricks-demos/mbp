# 2026-11-24 — Initial Design

## Context
- First session of the project. Done in a **different workspace** from the one the build will run in; the work reached this workspace through Git.
- Commit `54818fd` ("add design for genie ontology modeled knowledge sdk"), 2026-11-24 14:07 UTC, on branch `mg-genie-ontology-modeled-knowledge-sdk`, pushed to `origin` (branch tracks the remote; PR not yet opened). 53 files changed, 3,316 insertions: `genie-ontology-sdk/**` plus a new row in the mbp root `README.md`.
- Scope: design only. No SDK runtime code, no deployed resources, no build-waves instance.

## Goal
Design the Genie Ontology SDK — a developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology — and make it ready to build with genie-build-waves.

## Changes
- Drafted the L100 system design (first as a canvas), then decomposed it into L200-A..H (one per wave group: input validation, domain research, supplemental context, deep EDA, MV synthesis, registration incl. Pages, agent curation/deployment, tuning).
- Resolved all 7 open design questions (table below).
- Wrote L300 session plans `docs/plans/01`-`10`, the plan `INDEX.md` (session order, waves, dependency graph) and the genie-build-waves manifest `docs/plans/waves.json` (hybrid workflow, 10 waves, 10 sessions, one session per wave, continuation passes on waves 3, 4, 6, 8).
- Research: metric view CI/CD best practices, Genie Agent API + native `genie_spaces` DAB deployment, semantic metadata strategy.
- Semantics: SDK glossary.
- Diagrams: 5 Mermaid sources (architecture, waves sequence, two-DAB model, forEach registration, CI/CD promotion), rendered to SVG/HTML via the mermaid.ink API (mermaid-py).
- Pitch: customer-facing standalone HTML overview (Databricks branded). A Genie Artifact version is referenced by the README but was not committed.
- Examples: DAB 1 (metric view registration: `generate_manifest` + forEach `register_single_mv` notebooks, job YAML), DAB 2 (Genie Agents via `genie_spaces`, `engine: direct`), sample `mv_sales_revenue.yml` with a materialization block, sample `sales_agent.geniespace.json`.
- README (SDK) with Documents/Research/Semantics/Pitch/Diagrams/Examples/Plans tables; root mbp README topic row; this session log and INDEX.

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Pages deployment | Include — full automation (Wave 5.5) |
| 2 | Domain/Subdomain registration | Hybrid — generate proposal, opt-in creation |
| 3 | Materialization | Include — auto-generate materialization blocks |
| 4 | SGT App integration | Defer — separate products |
| 5 | Genie Observability | Defer — wait for native Genie Agent tracing |
| 6 | Incremental re-runs | Full regeneration (idempotent) |
| 7 | Multi-workspace deployment | Single workspace v1 |

## Verification
- All files written under `mbp/genie-ontology-sdk/` and committed in `54818fd`.
- Follows mbp layout conventions: README with tables, `docs/`, `examples/`, `docs/sessions/`.
- Not done in that session: `validate_manifest` on `waves.json`, `bundle validate` on the examples.

## Observations
- The forEach task pattern for MV registration is well-proven in genie-build-waves
- Native DAB `genie_spaces` resource with `file_path` is cleaner than REST API calls
- Materialization auto-detection is a differentiator — most manual standups skip this
- The 50 MV threshold for agent splitting needs empirical validation across domains

## Follow-ups
- [x] Write L200-A through L200-H design documents
- [x] Build example notebooks (generate_manifest.py, register_single_mv.py)
- [x] Create the Genie Build Waves manifest (waves.json) for the SDK pipeline
- [x] Render Mermaid diagrams to SVG/HTML (mermaid-py via mermaid.ink API)
- [x] Add to root README topic table
- [x] Create feature branch (`mg-genie-ontology-modeled-knowledge-sdk`, not `mg-genie-ontology-sdk`)
- [x] Push to GitHub (`54818fd`)
- [ ] Open PR to `main` (owner merges)
- [ ] Fix the review findings below, then deploy a genie-build-waves instance and run setup

## Design review findings

Review done 2026-11-24 in the build workspace, after the design arrived through Git. Method: read README, L100, plans INDEX, `waves.json`, examples; ran genie-build-waves `waves_manifest.validate_manifest` (from `mbp/genie-build-waves/src/notebooks`) on `waves.json`; compared with `genie-build-waves/docs/manifest-schema.md`. L200 docs and individual plans were only searched (grep), not read in full.

- `validate_manifest`: **1 error, 0 warnings** — wave `"5.5"`: wave_id must be letters, digits, `_` or `-`. The job would have 106 tasks (limit 1,000).
- Waves execute sequentially, so the "Waves 1-3 run in parallel" note in `docs/plans/INDEX.md` does not hold; parallelism needs one wave with 3 sessions.
- Plan 01 creates a Git branch; build-waves sessions are Git read-only (branch is a job parameter, integrator is the only committer).
- File-writing sessions are `execute` mode with only `owned_assets`; deploying sessions (06, 09, 10) lack `allow_deploy`.
- Open design question: what `build_root` is for a pipeline run (SDK folder vs. a separate target repo), since outputs are customer-specific.
- Hygiene: "Databricks Asset Bundles" wording, a customer name in L100 decision 3, wrong "Rapid Ontology Standup" link, missing Genie Artifact file, internal cross-references, example bundles with undeclared variables / missing smoke-test SQL / missing `agents/` folder.

Full list and next steps: [PROJECT_MEMORY.md](../../PROJECT_MEMORY.md).

## Files created this review
- `PROJECT_MEMORY.md` (new)
- this file (expanded)
