# Profile: samples.bakehouse.sales_customers

* Rows: 300 | Size: 20054 bytes | Files: 1 | Figures: exact
* Grain: one row per customer | Primary key: `customerID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: rebuilt by `CREATE OR REPLACE TABLE AS SELECT` about daily (50 data commits in the last 100 history entries, 2026-06-18 to 2026-09-14), last data write 2026-09-14 (DESCRIBE HISTORY). Content is static synthetic data.
* No clustering or partition columns. No declared PK/FK constraints.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| customerID | bigint | 0.0 | 300 | 1.0 | key | grain key |
| first_name | string | 0.0 | 180 | 0.6 | text | sensitive (values withheld); avg length 6.0 |
| last_name | string | 0.0 | 216 | 0.72 | text | sensitive (values withheld); avg length 6.1 |
| email_address | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 21.6 |
| phone_number | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 16.2 |
| address | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 23.0 |
| city | string | 0.0 | 297 | 0.99 | text | sensitive (values withheld); 297 distinct (> 100), not a reference label; avg length 11.8 |
| state | string | 0.0 | 98 | 0.33 | dimension | state / prefecture / region; mixed full names and abbreviations |
| country | string | 0.0 | 3 | 0.01 | dimension | customer country |
| continent | string | 0.0 | 3 | 0.01 | dimension | 1:1 with country |
| postal_zip_code | bigint | 0.0 | 300 | 1.0 | text | sensitive (values withheld) |
| gender | string | 0.0 | 2 | 0.007 | dimension | |

## Value distributions
* `country` (3): Australia 108 (36.0%), USA 99 (33.0%), Japan 93 (31.0%).
* `continent` (3): Oceania 108, North America 99, Asia 93 (maps 1:1 to country).
* `gender` (2): female 151 (50.33%), male 149 (49.67%).
* `state` (98, top 20): Washington 10, Arizona 8, Hawaii 7, Oregon 7, Nevada 7, Kentucky 7, Illinois 6, Missouri 6, Michigan 6, Arkansas 6, New Mexico 6, Kansas 6, California 6, Iowa 6, Ohio 6, MS 5, Maine 5, Texas 5, Massachusetts 5, Mississippi 5.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| customerID | referenced by samples.bakehouse.sales_transactions.customerID (fact -> this table) | 0.0 (unreferenced_rate 0.0) | many_to_one |

## Coded values
* `gender`: `female` 151, `male` 149. Meaning: self-describing.
* `country`: `Australia` 108, `USA` 99, `Japan` 93. Note `USA` here vs `US` in sales_franchises.country.
* `continent`: `Oceania` 108, `North America` 99, `Asia` 93.

## Lineage
upstream_tables: 0, downstream_tables: 85, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 2230, users_30d: 44. Common join/filter columns: none appear in `JOIN ... ON` or `WHERE` in 2+ of the 6 distinct query shapes in the 20-statement sample.

## Data quality flags
* `state` mixes full names and abbreviations (e.g. both `MS` and `Mississippi`); normalize before using as a dimension.
* `country` label `USA` differs from `US` in sales_franchises; do not join or compare countries across the two tables without mapping.
* Every customer buys at more than one franchise (all 300; max 18 franchises per customer): customer -> franchise is not a hierarchy.
* All 300 customers have at least one transaction (Active Customer Rate over the full window = 100%).

## Materialization signals
* `fan_out`: dimension reached from sales_transactions; customer counts through the fact need count(DISTINCT customerID).
* Candidate dimensions: `country`, `continent`, `gender`, `state` (after normalization).
