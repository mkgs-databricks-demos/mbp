# Project Memory — genie-ontology-sdk

Living memory for the Genie Ontology SDK. Read this before any session, and list it in `docs/plans/waves.json` `context_files`. Specific IDs (commits, runs, jobs, workspaces) belong in `docs/sessions/`, not here — `mbp` is customer-facing and must stay generic.

## Purpose

A developer toolkit that automates the standup of modeled knowledge for Genie Ontology: Unity Catalog source assets + supplemental business context -> parameterized metric views -> UC Pages -> curated Genie Agents -> an initial tuning plan. It codifies the Rapid Ontology Standup methodology and is executed by [genie-build-waves](../genie-build-waves).

## Status

* Phase: **build-0 planned; genie-build-waves instance deployed (dev), setup not yet run, no build run yet**. Build, smoke and setup jobs exist under the instance's own bundle root (`instance_suffix` `-genie-ontology-sdk`); job ids are in the [instance deployment session summary](docs/sessions/2026-11-24_build-waves-instance-deploy.md). The vars file lives outside this repo (it holds workspace paths).
* Build-0 executor: an external monitor agent (Devin) at **level 4** (acts for the owner: starts the build, repairs, pushes small fixes, escalates only on the monitor skill's stop conditions). Needs `monitor_principal` + `monitor_job_level=CAN_MANAGE_RUN` in the vars file, a redeploy, setup, and `CAN_READ` on `build_root` for the monitor principal.
* Build-0 = build the reusable SDK, then dogfood it end to end on `samples.tpch` into `examples/tpch/`. 11 waves (`0-0`..`0-10`), 19 sessions, hybrid workflow. `validate_manifest`: 0 errors, 0 warnings, 100 job tasks.
* **Manual prerequisite before wave 0-3 (done 2026-11-24):** the owner writes the gitignored `examples/tpch/ontology-metric-views/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `warehouse_id`) and `examples/tpch/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `schema` = dev-prefixed metric view schema, `warehouse_id`, `curator_group`). Workspace-specific values never go in committed files.
* History: see [docs/sessions/INDEX.md](docs/sessions/INDEX.md).
* Code review of the build-0 SDK (best practices, genie-build-waves coupling, customer path, prioritized improvements incl. Unity Gateway skills publishing): [docs/reviews/2026-11-25_build-0-sdk-review.md](docs/reviews/2026-11-25_build-0-sdk-review.md).

## Layout

| Path | Contents |
|---|---|
| `docs/design/` | L100 system design + L200-A..H, one per wave group |
| `docs/plans/` | Build-0 manifest `waves.json`, `INDEX.md` (wave map + cross-session contracts), plans in `build-0/` |
| `docs/design/l300-pipeline/` | Original pipeline-run plans 01-10, INDEX, waves.json (reference only; session 08 turns them into `templates/run/`) |
| `src/`, `tests/`, `skills/`, `templates/`, `notebooks/`, `examples/tpch/` | Created by build-0 (see `docs/plans/INDEX.md`) |
| `docs/research/` | MV CI/CD, Genie Agent API + DAB deployment, semantic metadata strategy |
| `docs/semantics/` | SDK glossary |
| `docs/diagrams/` | 5 diagrams as Mermaid source, SVG, HTML |
| `docs/pitch/` | Customer-facing standalone HTML overview |
| `docs/sessions/` | Session summaries + INDEX (reverse-chronological) |
| `examples/` | DAB 1 (metric view registration, forEach), DAB 2 (Genie Agents via `genie_spaces`), sample MV YAML, sample `.geniespace.json` |

## Architecture (from L100)

* **Inputs:** `source_catalogs` / `source_schemas` / `source_tables`, `repo_path`, `target_catalog`, `target_schema`, `domain_context`; optional `supplemental_volume_dirs`, `dashboard_inputs`, `source_catalog_for_reads`, `source_schema_for_reads`, `warehouse_id`, `max_metric_views_per_agent` (default 50).
* **Zero hardcoding:** MV YAML `source:` references are parameterized; the catalog is the environment discriminator (dev -> tst -> uat -> prd).
* **Two bundles:** DAB 1 owns MV YAMLs + a forEach registration job (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`, smoke test). DAB 2 owns `.geniespace.json` files deployed with the `genie_spaces` resource (`file_path`, `engine: direct`).
* **Waves:** 0 init/scaffold, 1 domain research, 2 supplemental context, 3 deep EDA, 4 MV synthesis (+ materialization blocks), 5 MV registration, 5.5 UC Pages, 6 agent curation (<=50 MVs per agent, else split by subdomain), 7 agent deployment, 8 tuning (fix MVs before agent instructions; 10-20 benchmark questions per agent; gate >= 70% accuracy).

## Resolved design decisions

| # | Topic | Decision |
|---|---|---|
| 1 | UC Pages | Include, fully automated (Wave 5.5) |
| 2 | Domains/subdomains | Hybrid: generate a proposal, opt-in creation |
| 3 | Materialization | Include: auto-generate `materialization:` blocks |
| 4 | Semantic Ground Truth app | Defer (separate products) |
| 5 | Genie observability | Defer until native agent tracing |
| 6 | Re-runs | Full regeneration (idempotent) |
| 7 | Multi-workspace | Single workspace in v1 |

## Pre-build review findings

Found in the first review of the design against genie-build-waves. Resolution status (build-0 planning):

| # | Status |
|---|---|
| 1-5, 13 | Resolved in the build-0 manifest. They remain in the reference `l300-pipeline/` files; session 08 fixes them in `templates/run/` |
| 6-7 | Resolved: `build_root` = this SDK folder; build-0 builds the SDK, then dogfoods it into `examples/tpch/` (generic public data). Customer runs scaffold their own project with the init tool |
| 8-11 | Resolved (README, L100, research doc edited) |
| 12 | Planned: sessions 06/07 build validate-clean templates; `examples/dab*` stay as historical examples |
| 14 | Resolved: `.gitignore` added |

Original findings: Details and evidence: [2026-11-24 initial design session](docs/sessions/2026-11-24_initial-design.md#design-review-findings).

**Blockers (setup will fail or the build will misbehave)**

1. `waves.json` wave_id `"5.5"` is rejected by `validate_manifest` (ids allow only letters, digits, `_`, `-`). Rename (e.g. `5-5`, or renumber 0-9). This is the only validator error.
2. Waves run **sequentially** in genie-build-waves. Waves 1, 2, 3 are separate waves, so they will not run in parallel as `docs/plans/INDEX.md` says. To parallelize, put sessions 02/03/04 in one wave with `concurrency: 3` and disjoint ownership (02 owns `docs/semantics/**`, and the wave 2 gate expects 03 to update `docs/semantics/` too).
3. Plan 01 runs `git checkout -b`. In git/hybrid workflows sessions are Git read-only; the build branch is a job parameter and only the integrator commits. Remove branch creation from Wave 0.
4. Execute-mode sessions that write repo files (01, 02, 03, 04, 10) declare only `owned_assets`, not `owned_paths`. Decide whether they should be `edit` sessions with `allow_execute: true` and `owned_paths`, so the integrator credits and commits their files.
5. Sessions 06, 09 and 10 deploy or run bundles per their scope text, but none sets `allow_deploy: true`. Add it (single deployer per wave), and consider `converge` + `runtime_targets` (`genie_space` target type exists) for 09.

**Design ambiguity to resolve first**

6. What is `build_root`? The manifest writes `ontology-metric-views/**`, `ontology-genie-agents/**`, `sdk_config.json` relative to `build_root`. If it is this folder, customer-specific output lands in `mbp`. Likely intent: this folder is the SDK (templates, plans, manifest); each run targets a separate customer repo (`repo_path`). Make that explicit, and decide how plans/manifest are copied or referenced from the target repo.
7. Building the SDK itself (code, skills, templates) vs. running the SDK pipeline for a domain are two different build-waves manifests. The current `waves.json` is the second kind.

**Hygiene**

8. "Databricks Asset Bundles" -> "Declarative Automation Bundles" (README line 5, L100 line 8, research/genie-agent-api-deployment.md line 8).
9. Customer name in L100 decision 3 rationale ("$60K/yr proof point") must be genericized (mbp rule).
10. README links "Rapid Ontology Standup" to `../genie-build-waves`; README references `genie_artifacts/...ga`, which is not in the repo.
11. L100 cross-references internal assets not in mbp (genie-production-readiness, Lattice, Frictionless Analyst Deployments).
12. Example bundles are unlikely to pass `bundle validate --strict` (not yet run): undeclared `${var.dev_warehouse_id}` / `${var.*_workspace_host}`, `workspace.host` set from a variable (verify support), missing `tests/test_metric_view_smoke.sql`, DAB 2 `file_path: ./agents/...` but no `agents/` folder in that bundle, no schema resource (`${resources.schemas.*}` convention).
13. `waves.json` has no `branch`, `bundle_target`, `validate_bundles` or `required_checks`; `owned_assets` uses `${var...}` placeholders, which the manifest does not resolve (informational only).
14. Add `.build-status/` to `.gitignore` before the first git/hybrid build.

## Conventions

* Feature branches only (`mg-genie-<desc>`); never commit to `main`; PR merged by the owner.
* No project-specific identifiers outside `docs/sessions/`.
* Spark Declarative Pipelines / Jobs / Declarative Automation Bundles terminology.
* Notebook paths in bundle YAML must match the extension on disk; run `bundle validate --strict` after edits.
* Tune metric views (comments, synonyms, measures) before adding Genie Agent instructions.

## Next steps

1. ~~Owner writes the two `variable-overrides.json` files~~ (done).
2. ~~Deploy a genie-build-waves instance~~ (done, first deploy; pre/post-deploy guard checks passed).
3. Redeploy with the monitor variables (web terminal, `scripts/deploy_instance.py`), grant the monitor principal `CAN_READ` on `build_root`, run setup (+ smoke).
4. Hand build-0 to the level 4 monitor; it starts the run and drives it to `BUILD_PASSED` or escalates.

## Build-0 open decisions (defaults applied)

* Deploy waves (0-6, 0-8, 0-9) use `allow_deploy` sessions + integrator `required_checks`, not `converge` + `runtime_targets` (those need workspace-specific names or ids in a committed file). Revisit in build 1 once ids are in session summaries.
* Tuning gate: scored results are required; accuracy below 70% becomes a build-1 backlog item.
* UC Pages (session 13) may be refused to job tasks: it may stop `blocked` without failing the wave.
* Monitor: changed by the owner (2026-11-24) from "no external monitor" to Devin at level 4, allowed to decide on its own to drive build-0 to completion within the monitor skill's guardrails and stop conditions.
