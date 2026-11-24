# Session 04: Deep EDA & Join Cardinality

## Scope
Profile every source table of `tpch_supply_chain` with read-only SQL and verify how the tables join. Write one profile per table and `docs/data_profiles/data_model_summary.md`. This session runs in parallel with sessions 02 and 03.

## Context
* Skill: load `skills/ontology-deep-eda/SKILL.md` and follow its per-table checklist, sampling rules and output contracts.
* Inputs: `docs/inputs_report.md` (table list) or `genie_ontology_sdk.config.expand_tables(cfg, ws)`; `warehouse_id` from `sdk_config.json` if set. KPI and join hints from `docs/research/` and `docs/context/` may be incomplete while sessions 02/03 run; verify what exists and note the rest.
* Join table contract in `data_model_summary.md`: columns `left`, `right`, `keys`, `verified_cardinality` (`many_to_one` / `one_to_one` / `many_to_many`), `orphan_rate`, `query_used`. The metric view validator reads `verified_cardinality` (rule MV005).
* Read-only SQL only (`SELECT`, `DESCRIBE`, `SHOW`, `EXPLAIN`). Record progress after each table so a continuation pass resumes at the next one.

## Tasks
1. Profile each table into `docs/data_profiles/<table>.md` (structure, nulls, grain, keys, cadence, volume, materialization signals).
2. Detect candidate joins and verify each cardinality with an exact grain query on the full table.
3. Write `docs/data_profiles/data_model_summary.md` with the join table and cross-table notes.

## Acceptance Criteria
- [ ] One profile per table in `docs/inputs_report.md`.
- [ ] Every join row has a `verified_cardinality` and the `query_used`.
- [ ] No row-level values from sensitive columns.

## Owned Paths
- `docs/data_profiles/**`

## Dependencies
- Session 01: `docs/inputs_report.md`.
