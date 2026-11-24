# Profile: samples.tpch.part

* Rows: 1,000,000 | Size: 20,824,976 bytes | Files: 1 | Figures: exact
* Grain: one row per part | Primary key: p_partkey (verified by pattern C: 0 duplicate rows) | Role: dimension
* Update cadence: static benchmark data, periodically rebuilt by `CREATE OR REPLACE TABLE AS SELECT` (last data write 2026-09-14); later commits are VACUUM only (DESCRIBE HISTORY, last 20 commits: VACUUM END x5, VACUUM START x5, CREATE OR REPLACE TABLE AS SELECT x10)
* Partitioning / clustering: none (Delta, no partition or clustering columns). Declared constraints: none (information_schema.table_constraints empty for samples.tpch)

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| p_partkey | bigint | 0.0000 | 1,000,000 | 1.0000 | key |  |
| p_name | string | 0.0000 | 999,962 | 1.0000 | text |  |
| p_mfgr | string | 0.0000 | 5 | 0.0000 | dimension |  |
| p_brand | string | 0.0000 | 25 | 0.0000 | dimension |  |
| p_type | string | 0.0000 | 150 | 0.0001 | dimension |  |
| p_size | int | 0.0000 | 50 | 0.0001 | dimension |  |
| p_container | string | 0.0000 | 40 | 0.0000 | dimension |  |
| p_retailprice | decimal(18,2) | 0.0000 | 25,691 | 0.0257 | measure |  |
| p_comment | string | 0.0000 | 477,637 | 0.4776 | text |  |

## Value distributions

* `p_mfgr` top values: Manufacturer#3 (20.06%), Manufacturer#4 (20.03%), Manufacturer#1 (19.99%), Manufacturer#2 (19.96%), Manufacturer#5 (19.96%)
* `p_brand` (25 values) top 20: Brand#33 (4.05%), Brand#35 (4.03%), Brand#12 (4.03%), Brand#44 (4.03%), Brand#21 (4.03%), Brand#14 (4.01%), Brand#43 (4.01%), Brand#24 (4.01%), Brand#51 (4.0%), Brand#42 (4.0%), Brand#31 (4.0%), Brand#41 (4.0%), Brand#34 (4.0%), Brand#45 (4.0%), Brand#54 (3.99%), Brand#52 (3.99%), Brand#23 (3.99%), Brand#53 (3.99%), Brand#13 (3.99%), Brand#55 (3.99%)
* `p_type`: 150 distinct values (>= 100, top values not listed)
* `p_size`: min 1, max 50, avg 25.5; roughly uniform (top value 38 at 2.04%)
* `p_container` (40 values) top 20: SM DRUM (2.53%), JUMBO CAN (2.53%), JUMBO JAR (2.52%), LG PACK (2.52%), MED PKG (2.51%), SM PACK (2.51%), LG PKG (2.51%), MED BOX (2.51%), JUMBO PACK (2.51%), WRAP BOX (2.51%), JUMBO BAG (2.51%), WRAP DRUM (2.51%), MED CASE (2.51%), JUMBO BOX (2.5%), LG JAR (2.5%), WRAP CAN (2.5%), MED BAG (2.5%), MED JAR (2.5%), WRAP PKG (2.5%), SM PKG (2.5%)
* `p_retailprice`: min 900.96, max 2098.99, avg 1499.50
* `p_name`, `p_comment`: free text; values not reported (counts only)

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| p_partkey | referenced by samples.tpch.lineitem.(l_partkey); 0 of these keys unreferenced | 0.0 | many_to_one (from lineitem) |
| p_partkey | referenced by samples.tpch.partsupp.(ps_partkey); 0 of these keys unreferenced | 0.0 | many_to_one (from partsupp) |

## Lineage
* Upstream: none recorded (system sample data). Downstream: 47 lineage edges in the last 90 days from `system.access.table_lineage` (notebooks, jobs, pipelines, dashboards, queries reading this table). Downstream table names are workspace-specific and not recorded here.

## Usage
* queries_30d: 2,526 | users_30d: 17 (`system.query.history`; the LIKE match on `tpch.part` also matches `tpch.partsupp`, so this is an upper bound)
* Common filter columns in a 400-statement sample of `samples.tpch` queries: `o_orderkey`, `l_orderkey`, `c_custkey` (key lookups). No `JOIN ... ON` columns were extracted from the sample; joins come from name matching and pattern G.

## Data quality flags
* None: no null keys, no duplicates on the grain, no orphan foreign keys.

## Materialization signals
* `fan_out` when measures are read from this side of its many_to_one joins
