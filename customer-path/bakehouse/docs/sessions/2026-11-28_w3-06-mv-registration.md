# 2026-11-28 — Wave 3, Session 06: Metric View Registration

* Build run: 409860738864401 (job 138308594859344, task `w3_session`), continuation 0, first attempt. Build started 2026-11-28T05:05:18Z at wave 3 (waves 0-2 disabled in this run).
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` at `02ab257`, read via the Repos API; no Git commands run).

## What was done

1. Skill: UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
2. Context read: manifest (wave 3, session 06), plan 06, `PROJECT_MEMORY.md`, previous session 06 status and summary (build run 244030216249267), `metric_views/manifest.json` (3 entries).
3. Prerequisite: SDK wheel `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` in `<sdk_volume_path>/.internal/` (HEAD 200). Overrides file not opened.
4. `bundle validate --strict --target dev`: `Validation OK!`.
5. `bundle deploy --target dev` (authorized): `3 created, 0 changed, 0 deleted, 0 unchanged`. The deploy found no prior deployment state (new deployment version record), so it created a new job `register_metric_views` (859595802942054) and re-applied the existing schema and its grants.
6. `bundle run register_metric_views --target dev --no-wait` (authorized), polled with the SDK: run 352877825862386 `TERMINATED/SUCCESS` (05:08:30Z to 05:10:41Z). All four tasks and all 3 for_each iterations `SUCCESS`.
7. Verified independently in `information_schema.tables`: the three views are `METRIC_VIEW`, `last_altered` 05:09:54Z (inside the run window). No `src/` folder in the bundle, so the job imported the installed wheel.
8. Updated `docs/registration/registration_results.md`. `docs/registration/resolved_target.json` already matches `bundle summary` (catalog `hls_fde_dev`, schema `dev_matthew_giglia_bakehouse_ontology`, warehouse `24087b85239cacac`); left unchanged.

## Problem: deployment state reset

* `bundle summary` before deploy showed both resources as `modified_status: created` with no ids, and the deploy created them instead of reporting them unchanged as in the previous build.
* Root cause (likely): the bundle's deployment state was not found (the deploy registered a new deployment version), so the CLI treated every resource as new. Not investigated further; outside this session's scope.
* Effect: the earlier job `[dev matthew_giglia] register_metric_views` (1000154254892119) still exists but is no longer tracked by the bundle. This session did not create it, so it was not deleted. Request to the owner below.

## Results

| item | result |
|---|---|
| registered views | 3 / 3 |
| smoke_test | 3 passed, 0 failed |
| cardinality_test | 2 checked, 0 failed |
| SDK imported | installed wheel 0.1.1 |

## Resolved targets

* Job `register_metric_views`: 859595802942054 (new; previous 1000154254892119).
* Schema: `hls_fde_dev.dev_matthew_giglia_bakehouse_ontology`.
* Warehouse id: `24087b85239cacac`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| wheel prerequisite present | pass |
| `bundle validate --strict --target dev` | pass |
| `bundle deploy --target dev` | pass |
| registration_job (SUCCESS after build start) | pass |
| mv_smoke (3/3 registered, smoke + cardinality SUCCESS, installed wheel) | pass |
| resolved_target | pass |

## Files

* `docs/registration/registration_results.md` (updated)

## Requests

* Owner: delete the orphaned job 1000154254892119 (older `[dev matthew_giglia] register_metric_views`, no longer in bundle state) and check why the `ontology-metric-views` dev deployment state was reset.
