# Project Memory — genie-ontology-modeled-knowledge-sdk

Living memory for the Genie Ontology Modeled Knowledge SDK. Read this before any session, and list it in `docs/plans/waves.json` `context_files`. Specific IDs (commits, runs, jobs, workspaces) belong in `docs/sessions/`, not here — `mbp` is customer-facing and must stay generic.

## Purpose

A developer toolkit that automates the standup of modeled knowledge for Genie Ontology: Unity Catalog source assets + supplemental business context -> parameterized metric views -> UC Pages -> curated Genie Agents -> an initial tuning plan. It codifies the Rapid Ontology Standup methodology and is executed by [genie-build-waves](../genie-build-waves/README.md).

## Status

* Phase: **build-0 complete.** Waves `0-0`..`0-10` passed their gates across three build runs (waves 0-6, 0-7 and 0-8 needed owner decisions or fixes and a re-run: a missing job-run approval, the UC Pages deferral, then a drifted agents overrides `schema`). Wave `0-10` (session 17) wrote the docs. Build-level verdict, owner decisions and open items: [build-0 wrap-up](docs/sessions/2026-11-25_build-0-wrap-up.md); run ids are in [docs/sessions/INDEX.md](docs/sessions/INDEX.md).
* **Renamed 2026-11-25** (before merge) from `genie-ontology-sdk` / package `genie_ontology_sdk` / "Genie Ontology SDK" to the current names, with no import alias. Session summaries written before the rename and the build-0 review keep the old names as history ([rename summary](docs/sessions/2026-11-25_rename-to-modeled-knowledge-sdk.md)).
* Build-0 delivered: library (`config`, `mv_yaml`, `manifest`, `geniespace`, `pages`, `benchmark`, `scaffold`), six `skills/ontology-*`, two bundle templates, the run kit (`templates/run/`), `notebooks/init_ontology_project`, and the TPC-H dogfood in `examples/tpch/` (23 glossary terms, 8 profiles, 7 metric views registered with smoke + cardinality pass, 1 Genie Agent with 3/3 probes, 93.3% baseline benchmark on 15 questions).
* Not done in build-0: UC Pages were dry-run only (no Discover domain for TPC-H; owner cell in `examples/tpch/docs/pages/pages_registration.md`). The run kit itself was never dogfooded (build-1 R3, R9).
* Guides: [README.md](README.md) (quickstart, layout) and [docs/usage.md](docs/usage.md) (end-to-end run).
* **Build-0 observations:** [docs/build-0-observations.md](docs/build-0-observations.md): 31 skill gaps / template fixes / platform limits from sessions 10a-16, plus owner items and notes from sessions 01-09.
* genie-build-waves instance: build, smoke and setup jobs exist under the instance's own bundle root (`instance_suffix` `-genie-ontology-sdk`, the pre-rename name); job ids are in the [instance deployment session summary](docs/sessions/2026-11-24_build-waves-instance-deploy.md). The vars file lives outside this repo (it holds workspace paths). **Its `build_root` and `manifest_path` still point at the pre-rename folder `../genie-ontology-sdk`:** update the vars file, redeploy and rerun setup before build 1 (owner decision).
* Build-0 executor: an external monitor agent (Devin) at **level 4** (acts for the owner: starts the build, repairs, pushes small fixes, escalates only on the monitor skill's stop conditions). Needs `monitor_principal` + `monitor_job_level=CAN_MANAGE_RUN` in the vars file, a redeploy, setup, and `CAN_READ` on `build_root` for the monitor principal.
* Build-0 = build the reusable SDK, then dogfood it end to end on `samples.tpch` into `examples/tpch/`. 11 waves (`0-0`..`0-10`), 19 sessions, hybrid workflow. `validate_manifest`: 0 errors, 0 warnings, 100 job tasks.
* **Manual prerequisite before wave 0-3 (done 2026-11-24):** the owner writes the gitignored `examples/tpch/ontology-metric-views/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `warehouse_id`) and `examples/tpch/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` (`catalog`, `schema` = dev-prefixed metric view schema, `warehouse_id`, `curator_group`). Workspace-specific values never go in committed files.
* History: see [docs/sessions/INDEX.md](docs/sessions/INDEX.md).
* Code review of the build-0 SDK (best practices, genie-build-waves coupling, customer path, prioritized improvements incl. Unity Gateway skills publishing): [docs/reviews/2026-11-25_build-0-sdk-review.md](docs/reviews/2026-11-25_build-0-sdk-review.md).
* **Build-1 requests** (owner-accepted, priority order R1-R9, each with change, files, acceptance criteria, dependencies, plus a sequencing table): [docs/plans/build-1/REQUESTS.md](docs/plans/build-1/REQUESTS.md).
* **Build-1 planned (2026-11-25, not run):** [docs/plans/build-1/INDEX.md](docs/plans/build-1/INDEX.md). 19 waves (`1-0`..`1-17` plus `1-2b`), sessions 18-45 plus 23b, appended to `docs/plans/waves.json` with the build-0 waves archived. R1-R9 + all build-0 observations + exhaustive MV-first tuning (100-498 questions, >= 3 tuning plans, stop at the asymptote) + an independent report simulation as the final evaluation; R9 last. `validate_manifest` / `validate_authorizations` 0/0, 172 job tasks. Owner prerequisites P1-1..P1-8 in the INDEX ([planning summary](docs/sessions/2026-11-25_build-1-planning.md)).

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
| `docs/reviews/` | Build-0 SDK code review |
| `Genie Code Start Session - DO NOT EDIT.ipynb` | Genie Code start-session notebook for this project; kept in the repo (owner decision). Never edit it |
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

Found in the first review of the design against genie-build-waves. **All 14 are closed** (status after build-0):

| # | Status |
|---|---|
| 1-5, 13 | Closed: resolved in the build-0 manifest, and session 08 fixed them in `templates/run/` (wave ids `0`..`6`, parallel discovery wave, no Git writes in plans, `edit` + `owned_paths` sessions, `allow_deploy` on single-session deploy waves, `bundle_target` / `validate_bundles` / `required_checks`). Remaining run-kit gaps are new findings, tracked as build-1 R3 |
| 6-7 | Closed: `build_root` = this SDK folder; build-0 built the SDK, then dogfooded it into `examples/tpch/`. Customer runs scaffold their own project with the init tool |
| 8-11 | Closed (README, L100, research doc edited) |
| 12 | Closed: sessions 06/07 built templates that pass `bundle validate --strict`; the TPC-H bundles deployed to dev. `examples/dab*` stay as historical examples |
| 14 | Closed: `.gitignore` added |

The list below is kept as the historical record. Details and evidence: [2026-11-24 initial design session](docs/sessions/2026-11-24_initial-design.md#design-review-findings).

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
2. ~~Deploy a genie-build-waves instance~~ (done).
3. ~~Run build-0 to completion~~ (done; waves 0-0..0-10 passed, 0-10 wrote the docs).
4. Owner review and merge of the build-0 feature branch PR (title and description drafted in the [close-out session](docs/sessions/2026-11-25_build-0-close-out.md)).
4b. Point the genie-build-waves instance at the renamed folder (vars file `build_root` / `manifest_path`), redeploy, rerun setup (build-1 P1-1).
5. Owner items from build-0: Pages are now session 31 of build 1 (drafts in the development domain); the placeholder deletion is build-1 P1-5.
6. ~~Plan build 1~~ (done 2026-11-25). Next: owner reviews the plan PR, completes P1-1..P1-5 and P1-8, then hands build 1 to Devin (level 4).

## Build-1 decisions

* **Development Pages domain (owner, 2026-11-25):** the metastore is at its Discover domain limit, so build 1 uses an existing domain the owner controls for Pages development and the TPC-H dogfood instead of creating one. Which domain, and why: [dev Pages domain session summary](docs/sessions/2026-11-25_build-1-dev-pages-domain.md). Rules: `DRAFT` pages only, record every created page id in `examples/tpch/docs/pages/pages_registration.md` for cleanup, keep the domain id out of committed SDK files.

* **Build-1 executor (owner, 2026-11-25):** Devin at level 4, as autonomous as possible: explicit owner authorizations per side effect, `monitor_may_authorize` on `owned_assets` for `jobs.run_now`, `bundle.deploy`, `volume.write`, `workspace.write`, `sql.ddl`, `uc_skills.publish`; owner-only actions (grants, permissions, secrets, destroy, deletes) stay `manual_prereqs`.
* **Build-1 hand-off (owner, 2026-11-25):** Devin level 4, `max_repairs` 12, escalation in the Devin session chat only, P1-6 (second-domain child build) done by Genie Code with the owner when Devin reaches wave 1-16 (the monitor skill forbids Devin deploys, setup runs and workspace writes), read-only review of the build branch changes after `BUILD_PASSED`. Instance retargeted and set up (P1-1); smoke test passed.
* **Build-1 defaults (proposed, owner did not object):** repo-root files staged under `ci/` and moved by the owner; asymptote = after >= 3 applied tuning plans, < 1.0 point gain in each of the last 2 iterations (or 100%) with holdout within 2.0 points of its best, at most 6 iterations; report simulation target 80%, recorded not gated.
* **SDK distribution (owner, 2026-11-25): ship both, wheel by default.** Projects install the versioned wheel (built by an SDK-root bundle `artifacts` block, uploaded to a UC volume through `workspace.artifact_path`, pinned by `sdk_version` in project bundles). Vendoring stays as an opt-in (`scaffold_project(vendor=True)`) for customers with no package egress or locked-down workspaces; `load_sdk()` keeps vendored-first, installed fallback. Request [R7a](docs/plans/build-1/REQUESTS.md#r7a-sdk-wheel-distribution); sessions 23 (code) and 23b (publish, wave 1-2b); the volume is a resource of the SDK bundle (no owner-created volume).
* **SDK schema (owner, 2026-11-25):** SDK setup asks the customer which catalog and schema to use, recommending a **new** schema, and deploys the SDK as a bundle at the SDK root with a **schema resource** (existing-schema mode as the alternative). One schema holds the published skills, the `sdk_wheels` volume and build-only `scratch_*` views. Build 1: session 18 deploys it in wave 1-0 from the owner's answers in the SDK bundle's gitignored dev overrides (P1-8: `sdk_catalog`, `sdk_schema`, `sdk_consumer_group`, `warehouse_id`); session 29 adds `notebooks/setup_sdk`.
* **Build-1 local targets:** workspace-specific values in gitignored files: the SDK bundle overrides above, the TPC-H overrides, and `.local/build-1.json` (`pages_domain_id`, later `customer_path_root`). The only committed file allowed a resolved dev schema name is `examples/tpch/docs/registration/resolved_target.json`.

## Build-0 open decisions (defaults applied)

* Deploy waves (0-6, 0-8, 0-9) use `allow_deploy` sessions + integrator `required_checks`, not `converge` + `runtime_targets` (those need workspace-specific names or ids in a committed file). Revisit in build 1 once ids are in session summaries.
* Tuning gate: scored results are required; accuracy below 70% becomes a build-1 backlog item.
* UC Pages (session 13) may be refused to job tasks: it may stop `blocked` without failing the wave.
* Monitor: changed by the owner (2026-11-24) from "no external monitor" to Devin at level 4, allowed to decide on its own to drive build-0 to completion within the monitor skill's guardrails and stop conditions.
