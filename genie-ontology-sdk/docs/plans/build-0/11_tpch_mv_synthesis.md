# Session 11: TPC-H Dogfood — Metric View Synthesis

## Scope
Dogfood the `ontology-mv-synthesis` skill. Turn the research, glossary and data profiles into parameterized metric view YAMLs under `examples/tpch/ontology-metric-views/metric_views/tpch_supply_chain/`, write `manifest.json`, and validate statically with the SDK.

## Context
* Load `skills/ontology-mv-synthesis/SKILL.md` (session 05b); use the `metric-views` platform skill for YAML syntax.
* Inputs: `examples/tpch/docs/research/**`, `docs/semantics/**`, `docs/data_profiles/**` (sessions 10a/10b).
* Expected scope: about 4-6 MVs, e.g. sales/revenue (lineitem x orders), orders, fulfillment/shipping, supplier cost (partsupp), customer by nation/region.
  * Joins only where `data_model_summary.md` has a `verified_cardinality`.
  * Add a `materialization` block where the skill's thresholds are met (`lineitem` is the large fact).
* Sources must use `${source_catalog}.${source_schema}.<table>`; never `samples.tpch` literally.

## Tasks
1. Write the MV YAMLs (explicit fields, comments on every measure, synonyms from the glossary).
2. `python -m genie_ontology_sdk.mv_yaml validate examples/tpch/ontology-metric-views/metric_views` -> 0 errors.
3. `manifest.write_manifest` -> `examples/tpch/ontology-metric-views/metric_views/manifest.json`.
4. Optional dry check (read-only): render one MV with `render_ddl` using `source_catalog=samples`, `source_schema=tpch` and run its source `SELECT` with LIMIT 5 to catch column typos. Do not CREATE anything.
5. A "Skill gaps" section in the session summary.

## Acceptance Criteria
- [ ] At least 4 YAMLs; `mv_yaml validate` exits 0 (warnings listed in the summary).
- [ ] `manifest.json` is valid per `manifest.validate_manifest_json`, with one entry per YAML.
- [ ] At least one MV has a materialization block, justified by a profile.
- [ ] `grep -r "samples.tpch" examples/tpch/ontology-metric-views/metric_views` returns nothing.

## Owned Paths / Assets
- `examples/tpch/ontology-metric-views/metric_views/**`

## Dependencies
- Sessions 10a, 10b (inputs); 02 (validator); 05b (skill).
