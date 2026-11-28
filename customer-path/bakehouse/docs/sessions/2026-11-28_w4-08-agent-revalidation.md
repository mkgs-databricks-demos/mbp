# 2026-11-28 — Wave 4, Session 08: Genie Agent Curation (re-validation)

* Build run: 409860738864401 (job 138308594859344, task `w4_session`), continuation 0, first attempt for this run.
* Mode: `edit` + `allow_execute` (no deploy). Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` at `027158a wave(3): 06`, read-only `git rev-parse` / `status` / `log`; no state-changing Git commands).
* Status: **pass** (already completed in build runs 38498872047824 and 244030216249267; outputs re-validated, no files changed).

## Context

* Since the last session 08 commit (`b189d89`), the only change under `ontology-genie-agents/`, `metric_views/` or `docs/domain_manifest.yml` is commit `02ab257`, which renamed the bundle in `ontology-genie-agents/databricks.yml` (not owned by this session). Agent file, resource entry and domain manifest are unaffected.
* In this run, session 06 redeployed `ontology-metric-views` (the deployment state had reset) and re-registered the same 3 views (run 352877825862386, SUCCESS, 3/3). `resolved_target.json` is unchanged.

## What was done

1. Skills: the UC skill ids for the session runner and `ontology-agent-curation` did not resolve through `readSkillFile`; used the workspace fallback for the runner (`mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`). No new curation was needed, so the curation rules were applied as recorded in the earlier session 08 summary.
2. Read `waves.json`, plan 08, `PROJECT_MEMORY.md`, `sdk_config.json`, this run's session 06 summary, the earlier session 08 summaries and status, `registration_results.md`, `manifest.json`, the resource YAML and README. No `hi_genie/` folder at the build root.
3. Installed SDK wheel 0.1.1 (SDK checkout `dist/`) into the session's serverless Python env only.
4. `plan_agents` over the 3 manifest entries (all registered) with `max_per_agent=30` -> 1 agent `bakehouse_retail_sales_agent` with 3 views, matching the committed file.
5. `validate_space` on the committed agent file: 0 errors. Identifiers are all `${target_catalog}.${target_schema}.<view>`.
6. `write_domain_manifest` to scratch with the committed descriptions: text identical to `docs/domain_manifest.yml`. Not rewritten.
7. README render step in-process: `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` -> `check: target schema and 3 identifiers resolve`, exit 0 (refreshed gitignored `.rendered/`).
8. Both example SQLs: `EXPLAIN` OK and run on the resolved dev schema (latest week 2024-05-13: 17715 vs 28509, -37.9%; top franchise Baked Bliss 6642). Same results as before.
9. `bundle validate --strict --target dev` (`bakehouse-ontology-genie-agents`): `Validation OK!`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| agent count rule (3 views <= 30 -> 1 agent, `plan_agents`) | pass |
| `validate_space` on committed file | pass (0 errors) |
| rebuilt domain manifest identical | pass |
| no literal `hls_fde`, `dev_matthew_giglia`, warehouse id or `samples.` in agent file or resources | pass |
| referenced views registered (`registration_results.md`, this run) | pass (3/3) |
| render `--check` with `resolved_target.json` | pass |
| example SQL `EXPLAIN` + run | pass (2/2) |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |

## Files

* None changed (only this summary and `.build-status/409860738864401/08.json`). `git status` shows no tracked changes. Gitignored render output `ontology-genie-agents/.rendered/` refreshed by the plan-mandated render step.

## Requests / notes

* None new. Owner decisions carried from session 05 (supplier coverage basis, approved supplier share basis) remain open.
* Session 09: the bundle is now named `bakehouse-ontology-genie-agents`; like the metric-views bundle in session 06, its first deploy may find no prior state and create a new Genie space rather than update the earlier one.
