# Profile: samples.tpch.partsupp

* Rows: 4,000,000 | Size: 143,561,015 bytes | Files: 2 | Figures: exact
* Grain: one row per part-supplier offer (part x supplier) | Primary key: ps_partkey, ps_suppkey (verified by pattern C: 0 duplicate rows) | Role: bridge
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14); later commits are VACUUM only (DESCRIBE HISTORY, last 20 commits: VACUUM END x9, VACUUM START x9, CREATE OR REPLACE TABLE AS SELECT x2)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| ps_partkey | bigint | 0.0000 | 1,000,000 | 0.2500 | fk (part of key) |  |
| ps_suppkey | bigint | 0.0000 | 50,000 | 0.0125 | fk (part of key) |  |
| ps_availqty | int | 0.0000 | 9,999 | 0.0025 | measure |  |
| ps_supplycost | decimal(18,2) | 0.0000 | 99,901 | 0.0250 | measure |  |
| ps_comment | string | 0.0000 | 3,978,444 | 0.9946 | text |  |

## Value distributions

* `ps_availqty`: min 1, max 9999, avg 5002.16
* `ps_supplycost`: min 1.00, max 1000.00, avg 500.56
* `ps_comment`: free text; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| ps_partkey, ps_suppkey | referenced by samples.tpch.lineitem.(l_partkey, l_suppkey); 1,950 of these keys unreferenced | 0.0 | many_to_one (from lineitem) |
| ps_partkey | samples.tpch.part.(p_partkey) | 0.0 | many_to_one |
| ps_suppkey | samples.tpch.supplier.(s_suppkey) | 0.0 | many_to_one |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 32 lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards, queries reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 610 | users_30d: 13 (`system.query.history`)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* 1,950 of 4,000,000 (ps_partkey, ps_suppkey) offers (0.05%) have no rows in `lineitem`; inner joins from `lineitem` drop them, so offer counts and inventory (`ps_availqty`) must come from this table
* `ps_availqty` and `ps_supplycost` are offer-level; summing them after joining from `lineitem` multiplies them by line count (up to 26 lines per offer)

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
