# Profile: samples.tpch.lineitem

* Rows: 29,999,795 | Size: 753,837,103 bytes | Files: 10 | Figures: sampled (1%) for null rates and distributions (`TABLESAMPLE (1 PERCENT) REPEATABLE (42)`, 299,998 rows); `approx_count_distinct` on the full table; grain and joins exact on the full table
* Grain: one row per order line (order x line number) | Primary key: l_orderkey, l_linenumber (verified by pattern C: 0 duplicate rows) | Role: fact
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14); later commits are VACUUM only (DESCRIBE HISTORY, last 20 commits: VACUUM END x9, VACUUM START x9, CREATE OR REPLACE TABLE AS SELECT x2)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| l_orderkey | bigint | 0.0000 | 7,034,375 (approx) | 0.2345 | fk (part of key) |  |
| l_partkey | bigint | 0.0000 | 925,738 (approx) | 0.0309 | fk |  |
| l_suppkey | bigint | 0.0000 | 50,113 (approx) | 0.0017 | fk |  |
| l_linenumber | int | 0.0000 | 7 (approx) | 0.0000 | key (composite) |  |
| l_quantity | decimal(18,2) | 0.0000 | 48 (approx) | 0.0000 | measure |  |
| l_extendedprice | decimal(18,2) | 0.0000 | 1,106,873 (approx) | 0.0369 | measure |  |
| l_discount | decimal(18,2) | 0.0000 | 11 (approx) | 0.0000 | measure |  |
| l_tax | decimal(18,2) | 0.0000 | 9 (approx) | 0.0000 | measure |  |
| l_returnflag | string | 0.0000 | 3 (approx) | 0.0000 | dimension |  |
| l_linestatus | string | 0.0000 | 2 (approx) | 0.0000 | dimension |  |
| l_shipdate | date | 0.0000 | 2,676 (approx) | 0.0001 | date |  |
| l_commitdate | date | 0.0000 | 2,615 (approx) | 0.0001 | date |  |
| l_receiptdate | date | 0.0000 | 2,721 (approx) | 0.0001 | date |  |
| l_shipinstruct | string | 0.0000 | 4 (approx) | 0.0000 | dimension |  |
| l_shipmode | string | 0.0000 | 7 (approx) | 0.0000 | dimension |  |
| l_comment | string | 0.0000 | 18,316,269 (approx) | 0.6105 | text |  |

Approx distinct counts carry estimation error (for example `l_suppkey` 50,113 vs 50,000 exact matched supplier keys in pattern G; `l_orderkey` matches all 7,500,000 orders exactly).

## Value distributions (sampled 1%)

* `l_linenumber`: min 1, max 7, avg 3.0; top values: 1 (24.89%), 2 (21.49%), 3 (17.85%), 4 (14.31%), 5 (10.68%), 6 (7.2%), 7 (3.57%)
* `l_quantity`: min 1.00, max 50.00, avg 25.49
* `l_extendedprice`: min 909.97, max 104348.50, avg 38226.98
* `l_discount`: min 0.00, max 0.10, avg 0.05
* `l_tax`: min 0.00, max 0.08, avg 0.04
* `l_returnflag` top values: N (50.79%), R (24.63%), A (24.59%)
* `l_linestatus` top values: O (50.15%), F (49.85%)
* `l_shipdate`: min 1992-01-03, max 1998-12-01
* `l_commitdate`: min 1992-01-31, max 1998-10-31
* `l_receiptdate`: min 1992-01-06, max 1998-12-28
* `l_shipinstruct` top values: COLLECT COD (25.1%), NONE (24.99%), TAKE BACK RETURN (24.97%), DELIVER IN PERSON (24.94%)
* `l_shipmode` top values: MAIL (14.36%), FOB (14.35%), AIR (14.3%), RAIL (14.3%), TRUCK (14.25%), REG AIR (14.24%), SHIP (14.2%)
* `l_comment`: free text; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| l_orderkey | samples.tpch.orders.(o_orderkey) | 0.0 | many_to_one |
| l_partkey, l_suppkey | samples.tpch.partsupp.(ps_partkey, ps_suppkey) | 0.0 | many_to_one |
| l_partkey | samples.tpch.part.(p_partkey) | 0.0 | many_to_one |
| l_suppkey | samples.tpch.supplier.(s_suppkey) | 0.0 | many_to_one |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 8,828 | users_30d: 38 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* None: no null keys, no duplicates on the grain, no orphan foreign keys.

## Materialization signals
* `large_table` (row_count > 10,000,000)
* `multi_join`: revenue by customer segment / nation / region needs lineitem -> orders -> customer -> nation -> region
