# Session 06 — Metric View Registration & Smoke Tests

**Wave:** 5 — Metric View Registration
**Mode:** execute
**Depends on:** 05
**Estimated effort:** Medium (~20 min)

## Goal

Register all metric views in Unity Catalog and validate they work.

## Context

Read `sdk_config.json` for target/source catalog/schema. Read `ontology-metric-views/metric_views/manifest.json` for the MV list.

## Tasks

### 1. Register Each Metric View

For each entry in manifest.json: read the YAML, substitute ${source_catalog}/${source_schema} parameters, execute `CREATE OR REPLACE VIEW target_catalog.target_schema.mv_name WITH METRICS LANGUAGE YAML AS $$ yaml_content $$`.

### 2. Smoke Test Each MV

Verify queryable: `SELECT * FROM mv LIMIT 5` and with MEASURE() syntax.

### 3. Join Cardinality Test

For MVs with joins, verify no measure inflation by comparing aggregation with and without the join.

### 4. Record Results

Write to `docs/tuning/registration_results.md`: list of all registered MVs with status, smoke test results, errors and resolutions.

## Pass Criteria

- [ ] All metric views registered without errors
- [ ] Every MV passes smoke test
- [ ] Join cardinality tests pass
- [ ] Registration results documented
