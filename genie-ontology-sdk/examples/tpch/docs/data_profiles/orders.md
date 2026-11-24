# Profile: samples.tpch.orders

* Rows: 7,500,000 | Size: 188,534,435 bytes | Files: 3 | Figures: exact
* Grain: one row per order | Primary key: o_orderkey (verified by pattern C: 0 duplicate rows) | Role: fact
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14); later commits are VACUUM only (DESCRIBE HISTORY, last 20 commits: VACUUM END x9, VACUUM START x9, CREATE OR REPLACE TABLE AS SELECT x2)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| o_orderkey | bigint | 0.0000 | 7,500,000 | 1.0000 | key |  |
| o_custkey | bigint | 0.0000 | 499,989 | 0.0667 | fk |  |
| o_orderstatus | string | 0.0000 | 3 | 0.0000 | dimension |  |
| o_totalprice | decimal(18,2) | 0.0000 | 6,671,609 | 0.8895 | measure |  |
| o_orderdate | date | 0.0000 | 2,406 | 0.0003 | date |  |
| o_orderpriority | string | 0.0000 | 5 | 0.0000 | dimension |  |
| o_clerk | string | 0.0000 | 5,000 | 0.0007 | text |  |
| o_shippriority | int | 0.0000 | 1 | 0.0000 | dimension |  |
| o_comment | string | 0.0000 | 7,212,284 | 0.9616 | text |  |

## Value distributions

* `o_orderstatus` top values: F (48.73%), O (48.72%), P (2.55%)
* `o_totalprice`: min 836.28, max 569370.40, avg 151125.23
* `o_orderdate`: min 1992-01-01, max 1998-08-02
* `o_orderpriority` top values: 4-NOT SPECIFIED (20.02%), 1-URGENT (20.01%), 5-LOW (20.0%), 2-HIGH (19.99%), 3-MEDIUM (19.98%)
* `o_shippriority`: constant 0 (100.0%)
* `o_clerk`, `o_comment`: identifying or free-text fields; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| o_custkey | samples.tpch.customer.(c_custkey) | 0.0 | many_to_one |
| o_orderkey | referenced by samples.tpch.lineitem.(l_orderkey); 0 of these keys unreferenced | 0.0 | many_to_one (from lineitem) |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 50+ (query LIMIT 50 reached) lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards, queries reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 10,545 | users_30d: 67 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* `o_shippriority` is constant (0): no analytic value as a dimension
* `o_totalprice` is an order-level total; summing it after joining to `lineitem` multiplies it by line count (up to 7)

## Materialization signals
* `multi_join`: revenue by customer segment / nation / region needs lineitem -> orders -> customer -> nation -> region
* `hot_table`: queries_30d in the top quartile of the 8 source tables
