# Profile: samples.tpch.customer

* Rows: 750,000 | Size: 40,135,843 bytes | Files: 1 | Figures: exact
* Grain: one row per customer | Primary key: c_custkey (verified by pattern C: 0 duplicate rows) | Role: dimension
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14); later commits are VACUUM only (DESCRIBE HISTORY, last 20 commits: VACUUM END x6, VACUUM START x6, CREATE OR REPLACE TABLE AS SELECT x8)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| c_custkey | bigint | 0.0000 | 750,000 | 1.0000 | key |  |
| c_name | string | 0.0000 | 750,000 | 1.0000 | text |  |
| c_address | string | 0.0000 | 750,000 | 1.0000 | text |  |
| c_nationkey | bigint | 0.0000 | 25 | 0.0000 | fk |  |
| c_phone | string | 0.0000 | 749,992 | 1.0000 | text |  |
| c_acctbal | decimal(18,2) | 0.0000 | 543,490 | 0.7247 | measure |  |
| c_mktsegment | string | 0.0000 | 5 | 0.0000 | dimension |  |
| c_comment | string | 0.0000 | 749,130 | 0.9988 | text |  |

## Value distributions

* `c_acctbal`: min -999.99, max 9999.99, avg 4501.03
* `c_mktsegment` top values: BUILDING (20.04%), FURNITURE (20.03%), MACHINERY (20.02%), HOUSEHOLD (19.96%), AUTOMOBILE (19.95%)
* `c_name`, `c_address`, `c_phone`, `c_comment`: identifying or free-text fields; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| c_custkey | referenced by samples.tpch.orders.(o_custkey); 250,011 of these keys unreferenced | 0.0 | many_to_one (from orders) |
| c_nationkey | samples.tpch.nation.(n_nationkey) | 0.0 | many_to_one |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (mostly untyped edges, plus notebooks, jobs and pipelines reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 7,875 | users_30d: 43 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* 250,011 of 750,000 `c_custkey` values (33.3%) have no rows in `orders`; inner joins from `orders` drop them, so customer counts must come from this table
* `c_phone` has 749,992 distinct values for 750,000 rows (8 fewer distinct values than rows, so some numbers repeat); not a key

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
