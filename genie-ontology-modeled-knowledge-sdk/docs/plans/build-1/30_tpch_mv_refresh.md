# Session 30: TPC-H Metric Views on the Wheel, Ratio Units, Re-registration

## Scope
Bring `examples/tpch/ontology-metric-views` up to the build-1 template, fix the ratio-unit observation, deploy to dev, upload the wheel, re-register all seven metric views, and write `resolved_target.json`. Deploy only this bundle.

## Context
* Build-0 observation 30 (q11 miss: `Return Rate` read as a percentage).
* Owner prerequisites P1-4 (`consumer_group` in the overrides) and P1-5 (placeholder deleted) are done before this wave.
* Authorized: `bundle.deploy` of this bundle (target dev), `jobs.run_now` of its `register_metric_views` job, `volume.write` to its `sdk_wheels` volume. Nothing else.
* Never print or commit `variable-overrides.json` values.

## Tasks
1. Apply the template changes from sessions 21 and 23 to the dogfood bundle by hand (not a re-scaffold over edited files): no vendored package, `sdk_wheel` variable, `sdk_wheels` volume, required `consumer_group`, optional `warehouse_id`, registration notebook exit value.
2. Obs 30: `Return Rate` / `Return Line Rate`: comment says "fraction 0-1" and a percentage `format` (pattern verified by session 25); `mv_yaml validate` exits 0.
3. `bundle validate --strict -t dev`, `bundle deploy -t dev` (max 4 attempts).
4. Build the wheel (`pip wheel --no-deps`) and upload it to the bundle's `sdk_wheels` volume path.
5. `bundle run register_metric_views -t dev`; fix and repeat until all views register with smoke + cardinality pass (max 4 attempts).
6. `gos-resolve-target --bundle examples/tpch/ontology-metric-views --target dev --out examples/tpch/docs/registration/resolved_target.json`, then check its schema holds all 7 views in `information_schema`.
7. Update `registration_results.md` (run id only in the session summary; the file shows status per view and that the wheel was installed).

## Acceptance Criteria
- [ ] Gate checks `registration_job`, `mv_smoke`, `resolved_target` pass.
- [ ] No `genie_ontology_modeled_knowledge_sdk_vendored` folder remains under `examples/tpch/`.

Note: `resolved_target.json` holds a resolved dev schema name. It is committed only under `examples/tpch/docs/registration/`; the wave 1-17 identifier grep excludes this one file (state that exclusion in your summary so session 45 applies it).

## Owned Paths / Assets
- `examples/tpch/ontology-metric-views/**`, `examples/tpch/docs/registration/**` (not `.databricks/`)
- Dev deployment of this bundle, its registration job, its `sdk_wheels` volume.

## Dependencies
- Sessions 21, 23, 25, 28, 29.
