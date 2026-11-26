# Session 30: TPC-H Metric Views on the Wheel, Ratio Units, Re-registration

## Scope
Move `examples/tpch/ontology-metric-views` to the published SDK wheel and the build-1 template, prove the move leaves the registered DDL identical, then fix the ratio-unit observation, re-register all seven metric views, and write `resolved_target.json`. Deploy only this bundle.

## Context
* Build-0 observation 30 (q11 miss: `Return Rate` read as a percentage).
* [REQUESTS R7a](REQUESTS.md#r7a-sdk-wheel-distribution): the wheel is the default; the TPC-H example uses it (no vendored copy). Session 23b published 0.1.0 to the SDK volume and recorded the stable path in `docs/distribution/wheel_publish.md`.
* **Consumer access (owner decision 2026-11-26, after run `288268071022101`):** `consumer_group` is replaced by the complex variable `schema_grants` (list of `{principal, privileges}`): the deploying developer in `dev` (`${workspace.current_user.userName}`), `account users` in other targets, overridable per target in `variable-overrides.json`. Workspace-local groups such as `admins` cannot hold Unity Catalog grants (the previous deploy failed with `PRINCIPAL_DOES_NOT_EXIST`). The owner already applied this to `examples/tpch/ontology-metric-views/databricks.yml` and `resources/ontology_schema.yml` in the working tree (uncommitted, inside this session's owned paths): keep those edits and commit them with yours.
* Owner prerequisites P1-4 (`sdk_volume_path` in the overrides, no `consumer_group` key) and P1-5 (placeholder agent file and the TPC-H vendored folder deleted) are done before this wave.
* Authorized: `bundle.deploy` of this bundle (target dev), `jobs.run_now` of its `register_metric_views` job. Nothing else (the wheel is already in the volume).
* Never print or commit `variable-overrides.json` values.

## Tasks
1. **Before any change:** capture the DDL each registered view would get with `mv_yaml.render_ddl` on the current YAML, **tokenized** (catalog and schema as `${target_catalog}.${target_schema}`), into `examples/tpch/docs/registration/ddl_before_wheel.sql`; cross-check one view against the registered definition (`DESCRIBE TABLE EXTENDED ... AS JSON` view text) and note the result.
2. Apply the template changes from sessions 21 and 23 to the dogfood bundle by hand (not a re-scaffold over edited files): the vendored folder `src/genie_ontology_modeled_knowledge_sdk_vendored/` is already gone (owner deletion in P1-5, because sessions cannot delete files; if it is still present, stop `blocked` and name the files, since `load_sdk()` prefers a vendored `mv_yaml.py`); `sdk_version` = `0.1.0`, `sdk_wheel`, `sdk_wheel_subpath` and `sdk_volume_path` variables, the job environment and `environment_key`s, `schema_grants` (already applied, see Context), optional `warehouse_id`, registration notebook exit value.
3. `bundle validate --strict -t dev`, `bundle deploy -t dev`, `bundle run register_metric_views -t dev` (max 4 attempts); confirm in the run output that the SDK was imported from the installed wheel (`__file__` under `site-packages`, `__version__` 0.1.0).
4. Capture `ddl_after_wheel.sql` the same way from the YAML the job registered; it must equal `ddl_before_wheel.sql` byte for byte (gate check `ddl_identical`).
5. **Then** obs 30: `Return Rate` / `Return Line Rate`: comment says "fraction 0-1" and a percentage `format` (pattern verified by session 25); `mv_yaml validate` exits 0; deploy and re-register until all views pass smoke + cardinality (max 4 attempts).
6. `gos-resolve-target --bundle examples/tpch/ontology-metric-views --target dev --out examples/tpch/docs/registration/resolved_target.json`, then check its schema holds all 7 views in `information_schema`.
7. Update `registration_results.md` (run id only in the session summary; the file shows status per view and that the wheel was installed).

## Acceptance Criteria
- [ ] Gate checks `registration_job`, `mv_smoke`, `resolved_target`, `ddl_identical` pass.
- [ ] No `genie_ontology_modeled_knowledge_sdk_vendored` folder remains under `examples/tpch/`.

Note: `resolved_target.json` holds a resolved dev schema name. It is committed only under `examples/tpch/docs/registration/`; the wave 1-17 identifier grep excludes this one file (state that exclusion in your summary so session 45 applies it).

## Owned Paths / Assets
- `examples/tpch/ontology-metric-views/**`, `examples/tpch/docs/registration/**` (not `.databricks/`)
- Dev deployment of this bundle and its registration job.

## Dependencies
- Sessions 21, 23, 23b (published wheel), 25, 28, 29.
