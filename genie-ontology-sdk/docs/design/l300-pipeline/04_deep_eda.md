# Session 04 — Deep EDA — Table Profiling & Relationship Detection

**Wave:** 3 — Deep Exploratory Data Analysis
**Mode:** execute
**Depends on:** 01
**Estimated effort:** Heavy (~30+ min, may need continuation)

## Goal

Profile every source table comprehensively. Detect cross-table relationships. Produce data profiles that drive metric view synthesis in Wave 4.

## Context

Read `sdk_config.json` for `all_tables`. This session may hit the step limit on large table sets; use continuation passes.

## Tasks

### 1. Per-Table Profiling

For each table: DESCRIBE EXTENDED, row count, DESCRIBE DETAIL, null rates per column, uniqueness ratios, value distributions for categorical columns (< 100 distinct values), lineage from system.access.table_lineage, usage from system.query.history, history from DESCRIBE HISTORY.

Write to: `docs/data_profiles/{table_name}.md`

### 2. Primary Key Detection

Test column combinations for uniqueness. Single columns with uniqueness_ratio = 1.0 are candidate PKs. Record the grain (what one row represents).

### 3. Cross-Table Relationship Detection

For each pair of tables: name matching (columns with matching names), value overlap (INTERSECT coverage), cardinality determination (many-to-one vs many-to-many).

### 4. Materialization Signal Detection

Flag: row count > 10M, complex multi-table joins (3+), one-to-many relationships, columns frequently in WHERE clauses.

### 5. Consolidated Summary

Write `docs/data_profiles/data_model_summary.md`: table inventory with row counts and grain, entity-relationship Mermaid diagram, verified join keys with cardinality, materialization candidates, data quality flags.

## Pass Criteria

- [ ] One profile per source table
- [ ] `data_model_summary.md` with cross-table analysis
- [ ] Primary key candidates identified
- [ ] Join key candidates with cardinality verification
- [ ] Materialization candidates flagged
