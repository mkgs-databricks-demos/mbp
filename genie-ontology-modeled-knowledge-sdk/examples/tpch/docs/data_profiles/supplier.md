# Profile: samples.tpch.supplier

* Rows: 50,000 | Size: 2,580,481 bytes | Files: 1 | Figures: exact
* Grain: one row per supplier | Primary key: s_suppkey (verified by pattern C: 0 duplicate rows) | Role: dimension
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14) (DESCRIBE HISTORY, last 20 commits: CREATE OR REPLACE TABLE AS SELECT x18, VACUUM END x1, VACUUM START x1)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| s_suppkey | bigint | 0.0000 | 50,000 | 1.0000 | key |  |
| s_name | string | 0.0000 | 50,000 | 1.0000 | text |  |
| s_address | string | 0.0000 | 50,000 | 1.0000 | text |  |
| s_nationkey | bigint | 0.0000 | 25 | 0.0005 | fk |  |
| s_phone | string | 0.0000 | 50,000 | 1.0000 | text |  |
| s_acctbal | decimal(18,2) | 0.0000 | 48,850 | 0.9770 | measure |  |
| s_comment | string | 0.0000 | 49,999 | 1.0000 | text |  |

## Value distributions

* `s_acctbal`: min -999.92, max 9999.72, avg 4513.77
* `s_name`, `s_address`, `s_phone`, `s_comment`: identifying or free-text fields; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| s_suppkey | referenced by samples.tpch.lineitem.(l_suppkey); 0 of these keys unreferenced | 0.0 | many_to_one (from lineitem) |
| s_suppkey | referenced by samples.tpch.partsupp.(ps_suppkey); 0 of these keys unreferenced | 0.0 | many_to_one (from partsupp) |
| s_nationkey | samples.tpch.nation.(n_nationkey) | 0.0 | many_to_one |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards, queries reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 1,110 | users_30d: 19 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* None: no null keys, no duplicates on the grain, no orphan foreign keys.

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
