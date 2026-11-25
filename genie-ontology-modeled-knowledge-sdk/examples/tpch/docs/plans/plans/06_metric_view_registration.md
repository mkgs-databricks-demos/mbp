# Session 06: Metric View Registration & Smoke Tests

## Scope
Deploy the `ontology-metric-views` bundle to the `dev` target and run its `register_metric_views` job. The job registers every metric view in `manifest.json` (`CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`), then runs the smoke and cardinality tests. Record the results in `docs/registration/`. This is the only session in its wave, because it deploys.

## Context
* Skill: none required. The bundle README (`ontology-metric-views/README.md`) documents the variables, the overrides file and the run command.
* Workspace values (catalog, warehouse) come from the gitignored `ontology-metric-views/.databricks/bundle/dev/variable-overrides.json`, written by the owner. Never print, edit or commit it. If it is missing, stop with `status: "blocked"`.
* Approvals: `bundle.deploy` of this bundle is implied by `allow_deploy`. Running the job is approved in the session's `authorizations` (rendered into the prompt). Deploy nothing else.
* Job tasks: `generate_manifest` -> `register_each_mv` (for_each) -> `smoke_test` -> `cardinality_test`.

## Tasks
1. From `ontology-metric-views/`, run `bundle validate --strict --target dev`, then `bundle deploy --target dev`.
2. Run `bundle run register_metric_views --target dev` and wait for it to finish.
3. On failure, read the failed task's error. A YAML defect is session 05's file: record a `request` to the owner (re-run wave 2) and stop with `status: "fail"`. Do not edit metric view YAML here.
4. Write `docs/registration/registration_results.md`: run id and result state, start time, per-view registered yes/no (fully qualified names written with `${target_catalog}.${target_schema}` tokens), and the smoke and cardinality task results with any failing view.

## Acceptance Criteria
- [ ] The `register_metric_views` run finished `SUCCESS` after this build run started.
- [ ] Every `manifest.json` entry is registered, and `smoke_test` and `cardinality_test` are `SUCCESS`.
- [ ] Deployed IDs are recorded under `resolved_targets` in the status file.

## Owned Paths
- `docs/registration/**`

## Dependencies
- Session 05: `ontology-metric-views/metric_views/**` and `manifest.json`.
