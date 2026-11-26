# Session 06: Metric View Registration & Smoke Tests

## Scope
Deploy the `ontology-metric-views` bundle to the `{{bundle_target}}` target and run its `register_metric_views` job. The job registers every metric view in `manifest.json` (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`), then runs the smoke and cardinality tests. Record the results in `docs/registration/`. This is the only session in its wave, because it deploys.

## Context
* Skill: none required. The bundle README (`ontology-metric-views/README.md`) documents the variables, the overrides file and the run command.
* Workspace values (catalog, warehouse) come from the gitignored `ontology-metric-views/.databricks/bundle/{{bundle_target}}/variable-overrides.json`, written by the owner. Never print, edit or commit it. If it is missing, stop with `status: "blocked"`.
* Approvals: `bundle.deploy` of `ontology-metric-views` and `jobs.run_now` of `register_metric_views` (both on `{{bundle_target}}`) are in the session's `authorizations` (rendered into the prompt). Deploy nothing else.
* SDK wheel prerequisite (wave `manual_prereqs`, wheel mode only): `genie_ontology_modeled_knowledge_sdk-{{sdk_version}}-py3-none-any.whl` is in the SDK `sdk_wheels` volume, `sdk_volume_path` is set in the overrides file, and the run-as principals have `READ VOLUME`. If it is missing, stop with `status: "blocked"`. A `vendor=True` project has no such prerequisite.
* Job tasks: `generate_manifest` -> `register_each_mv` (for_each) -> `smoke_test` -> `cardinality_test`.

## Tasks
1. From `ontology-metric-views/`, run `bundle validate --strict --target {{bundle_target}}`, then `bundle deploy --target {{bundle_target}}`.
2. Run `bundle run register_metric_views --target {{bundle_target}}` and wait for it to finish.
3. On failure, read the failed task's error. A YAML defect is session 05's file: record a `request` to the owner (re-run wave 2) and stop with `status: "fail"`. Do not edit metric view YAML here.
4. Write `docs/registration/registration_results.md`: run id and result state, start time, per-view registered yes/no (fully qualified names written with `${target_catalog}.${target_schema}` tokens), and the smoke and cardinality task results with any failing view, plus the SDK the job imported (installed wheel version, or vendored).
5. Write `docs/registration/resolved_target.json` with `catalog`, `schema` and `warehouse_id` resolved from `bundle summary --target {{bundle_target}}`. Later sessions render agents with `geniespace render --params docs/registration/resolved_target.json --check`.

## Acceptance Criteria
- [ ] The `register_metric_views` run finished `SUCCESS` after this build run started.
- [ ] Every `manifest.json` entry is registered, and `smoke_test` and `cardinality_test` are `SUCCESS`; the job imported the installed SDK wheel (wheel mode).
- [ ] `docs/registration/resolved_target.json` exists.
- [ ] Deployed IDs are recorded under `resolved_targets` in the status file.

## Owned Paths
- `docs/registration/**`

## Dependencies
- Session 05: `ontology-metric-views/metric_views/**` and `manifest.json`.
