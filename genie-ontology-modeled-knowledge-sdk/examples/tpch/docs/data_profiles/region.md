# Profile: samples.tpch.region

* Rows: 5 | Size: 1,832 bytes | Files: 1 | Figures: exact
* Grain: one row per region | Primary key: r_regionkey (verified by pattern C: 0 duplicate rows) | Role: dimension
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14) (DESCRIBE HISTORY, last 20 commits: CREATE OR REPLACE TABLE AS SELECT x20)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| r_regionkey | bigint | 0.0000 | 5 | 1.0000 | key |  |
| r_name | string | 0.0000 | 5 | 1.0000 | dimension |  |
| r_comment | string | 0.0000 | 5 | 1.0000 | text |  |

## Value distributions

* `r_name` top values: EUROPE (20.0%), AMERICA (20.0%), AFRICA (20.0%), ASIA (20.0%), MIDDLE EAST (20.0%)
* `r_comment`: free text; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| r_regionkey | referenced by samples.tpch.nation.(n_regionkey); 0 of these keys unreferenced | 0.0 | many_to_one (from nation) |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards, queries reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 6,117 | users_30d: 26 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* None: no null keys, no duplicates on the grain, no orphan foreign keys.

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
