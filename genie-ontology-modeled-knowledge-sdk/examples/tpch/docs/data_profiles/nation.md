# Profile: samples.tpch.nation

* Rows: 25 | Size: 2,939 bytes | Files: 1 | Figures: exact
* Grain: one row per nation | Primary key: n_nationkey (verified by pattern C: 0 duplicate rows) | Role: dimension
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14) (DESCRIBE HISTORY, last 20 commits: CREATE OR REPLACE TABLE AS SELECT x20)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| n_nationkey | bigint | 0.0000 | 25 | 1.0000 | key |  |
| n_name | string | 0.0000 | 25 | 1.0000 | dimension |  |
| n_regionkey | bigint | 0.0000 | 5 | 0.2000 | fk |  |
| n_comment | string | 0.0000 | 25 | 1.0000 | text |  |

## Value distributions

* `n_name`: 25 values, one row each (4.0% each); first 20 by the top-N query: CHINA, JORDAN, MOZAMBIQUE, PERU, IRAN, JAPAN, INDONESIA, MOROCCO, INDIA, GERMANY, ARGENTINA, ETHIOPIA, EGYPT, IRAQ, ALGERIA, FRANCE, CANADA, KENYA, BRAZIL, ROMANIA
* `n_comment`: free text; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| n_nationkey | referenced by samples.tpch.customer.(c_nationkey); 0 of these keys unreferenced | 0.0 | many_to_one (from customer) |
| n_nationkey | referenced by samples.tpch.supplier.(s_nationkey); 0 of these keys unreferenced | 0.0 | many_to_one (from supplier) |
| n_regionkey | samples.tpch.region.(r_regionkey) | 0.0 | many_to_one |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 188,680 | users_30d: 37 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* `nation` is reached from both `customer` and `supplier`: a metric view joining both must alias it twice (customer nation vs supplier nation)

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
* `hot_table`: queries_30d in the top quartile of the 8 source tables (highest: 188,680 queries in 30 days)
