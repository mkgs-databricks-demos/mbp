# 2026-11-27 — Wave 3, Session 06: Metric View Registration & Smoke Tests

* Build run: 38498872047824 (job 138308594859344, task `w3_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` confirmed on that branch at `b1ec1c3 wave(2): 05` with a read-only `git rev-parse`; no state-changing Git commands).

## What was done

1. Skill: the UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
2. Context read: manifest (wave 3, session 06), plan `plans/06_metric_view_registration.md`, `PROJECT_MEMORY.md`, session 05 summary, bundle `databricks.yml`, job YAML, `metric_views/manifest.json`.
3. Prerequisites: `ontology-metric-views/.databricks/bundle/dev/variable-overrides.json` exists (only key names checked, values not printed). Wave `manual_prereqs` P-wheel: `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` is present in `<sdk_volume_path>/.internal/` and was readable by the build's run-as user.
4. `bundle validate --strict --target dev`: `Validation OK!`.
5. `bundle deploy --target dev` (authorized, tier 2): `0 created, 3 changed, 0 deleted` (schema, schema grants, job). Source-linked deployment.
6. `bundle run register_metric_views --target dev --no-wait` (authorized), polled with the SDK: run 283984710672415 finished `SUCCESS`; all four tasks `SUCCESS`.
7. Verified in UC: the three views exist as `METRIC_VIEW` in the target schema, `last_altered` inside the run window.
8. Wrote `docs/registration/registration_results.md` and `docs/registration/resolved_target.json`.

## Results

| item | result |
|---|---|
| registered views | 3 / 3 (`mv_bakehouse_customer_activity`, `mv_bakehouse_sales`, `mv_bakehouse_supplier_coverage`) |
| smoke_test | 3 passed, 0 failed |
| cardinality_test | 2 checked (views with joins), 0 failed |
| SDK imported | installed wheel 0.1.1 (no vendored `src/` folder in the bundle or deployed files) |

## Resolved targets (from `bundle summary --target dev`)

* Job `register_metric_views`: id 1000154254892119 (`[dev matthew_giglia] register_metric_views`).
* Schema `ontology_schema`: `hls_fde_dev.dev_matthew_giglia_bakehouse_ontology`.
* Warehouse id (variable): `24087b85239cacac`.

## Observations

* The target schema holds 161 objects in `information_schema.tables`, including many `__..._metric_view_mat_...` materialized views (only part of the listing was inspected), besides the 3 views this session registered; the others were not created by this session. Not touched. The owner may want to check where they come from.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| wheel prerequisite present | pass |
| `bundle validate --strict --target dev` | pass |
| `bundle deploy --target dev` | pass |
| registration run SUCCESS after build start (03:54:13Z > 03:08:29Z) | pass |
| every manifest entry registered; smoke + cardinality SUCCESS; installed wheel | pass |
| `resolved_target.json` written | pass |

## Files

* `docs/registration/registration_results.md` (new)
* `docs/registration/resolved_target.json` (new)

## Requests

None.
