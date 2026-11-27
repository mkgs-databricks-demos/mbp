# Profile: samples.bakehouse.sales_customers

* Rows: 300 | Size: 20054 bytes | Files: 1 | Figures: exact
* Grain: one row per customer | Primary key: `customerID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: static content, periodically rebuilt by full replace: 50 `CREATE OR REPLACE TABLE AS SELECT` data commits between 2026-06-18 and 2026-09-14, last data write 2026-09-14 (DESCRIBE HISTORY; maintenance commits ignored).
* Declared constraints: none. Table comment is a generic dataset description; no column comments.
* Clustering / partitioning: none.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| customerID | bigint | 0.0 | 300 | 1.0 | key | primary key; range 2000000-2000299 |
| first_name | string | 0.0 | 180 | 0.6 | text | sensitive (values withheld); avg length 6.0 |
| last_name | string | 0.0 | 216 | 0.72 | text | sensitive (values withheld); avg length 6.1 |
| email_address | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 21.6 |
| phone_number | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 16.2 |
| address | string | 0.0 | 300 | 1.0 | text | sensitive (values withheld); avg length 22.9 |
| city | string | 0.0 | 297 | 0.99 | text | sensitive (values withheld); 297 distinct, not a reference label; avg length 11.8 |
| state | string | 0.0 | 98 | 0.3267 | dimension | customer state / region; avg length 6.0 |
| country | string | 0.0 | 3 | 0.01 | dimension | customer country |
| continent | string | 0.0 | 3 | 0.01 | dimension | 1:1 with country |
| postal_zip_code | bigint | 0.0 | 300 | 1.0 | text | sensitive (values withheld) - token `zip` |
| gender | string | 0.0 | 2 | 0.0067 | dimension | customer gender |

## Value distributions
* `country`: Australia 108 (36.0%), USA 99 (33.0%), Japan 93 (31.0%).
* `continent`: Oceania 108 (36.0%), North America 99 (33.0%), Asia 93 (31.0%) (maps 1:1 to country).
* `gender`: female 151 (50.33%), male 149 (49.67%).
* `state`: 98 distinct values, most frequent Washington 10, Arizona 8, then Hawaii / Kentucky / Nevada / Oregon 7 each; mix of US states and non-US regions.
* Sensitive columns: values, min/max withheld.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| customerID | referenced by samples.bakehouse.sales_transactions.customerID | 0.0 (unreferenced customers: 0 of 300) | many_to_one (transactions -> customers) |

## Coded values
* `country`: `Australia` 108, `USA` 99, `Japan` 93. Note: franchises use `US`, customers use `USA` for the same country.
* `continent`: `Oceania` 108, `North America` 99, `Asia` 93.
* `gender`: `female` 151, `male` 149.

## Lineage
upstream_tables: 0, downstream_tables: 85, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 2226, users_30d: 44. Common join/filter columns (sample of 20 distinct query shapes, 181 shapes overall): join `customerID` (10 shapes); no filter column in 2+ shapes.

## Data quality flags
* Country naming differs from `sales_franchises.country` (`USA` vs `US`): customer-country vs franchise-country comparisons need a mapping.
* Customer country is not the store country: customers buy at franchises in many countries (e.g. Australian customers at Japanese stores, 515 transactions). Do not use customer geography as a proxy for sales geography.
* 7 of 12 columns are PII; exclude them from metric view dimensions.
* No nulls, no duplicate keys.

## Materialization signals
none (300 rows; not in the top ceil(4/4) = 1 by usage).
