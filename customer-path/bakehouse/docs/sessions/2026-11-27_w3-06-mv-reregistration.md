# 2026-11-27 — Wave 3, Session 06: Metric View Re-registration

* Build run: 244030216249267 (job 138308594859344, task `w3_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` at `8fdfc37`, read via the Repos API; no state-changing Git commands).
* Session 06 already passed in build run 38498872047824. The wave 3 gate needs a registration run that finished after *this* build run started, so the bundle was redeployed and the job re-run. Metric view YAML is unchanged (session 05 in this run re-validated it with no edits).

## What was done

1. Skill: UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
2. Context read: manifest (wave 3, session 06), plan 06, `PROJECT_MEMORY.md`, session 05 status for this run, earlier session 06 summary and status (run 38498872047824).
3. Prerequisites: `variable-overrides.json` exists (not opened); SDK wheel `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` present in `<sdk_volume_path>/.internal/` (HEAD 200).
4. `bundle validate --strict --target dev`: `Validation OK!`.
5. `bundle deploy --target dev` (authorized): `0 created, 0 changed, 0 deleted, 3 unchanged`.
6. `bundle run register_metric_views --target dev --no-wait` (authorized), polled with the SDK: run 377694921681813 `TERMINATED/SUCCESS` (13:42:50Z to 13:45:01Z; build run started 13:00:48Z). All four tasks and all 3 for_each iterations `SUCCESS`.
7. Verified independently in `information_schema.tables`: the three views are `METRIC_VIEW`, `last_altered` 13:44:12Z (inside the run window). No `src/` folder in the bundle, so the job imported the installed wheel.
8. Updated `docs/registration/registration_results.md` with this run's ids and times. `docs/registration/resolved_target.json` already matches `bundle summary` (catalog `hls_fde_dev`, schema `dev_matthew_giglia_bakehouse_ontology`, warehouse `24087b85239cacac`), left unchanged.

## Results

| item | result |
|---|---|
| registered views | 3 / 3 |
| smoke_test | 3 passed, 0 failed |
| cardinality_test | 2 checked, 0 failed |
| SDK imported | installed wheel 0.1.1 |

## Resolved targets

* Job `register_metric_views`: 1000154254892119.
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

None.
