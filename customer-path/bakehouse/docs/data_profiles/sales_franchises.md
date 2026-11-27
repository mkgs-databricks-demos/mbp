# Profile: samples.bakehouse.sales_franchises

* Rows: 48 | Size: 5472 bytes | Files: 1 | Figures: exact
* Grain: one row per franchise store | Primary key: `franchiseID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: static content, periodically rebuilt by full replace: 50 `CREATE OR REPLACE TABLE AS SELECT` data commits between 2026-06-18 and 2026-09-14, last data write 2026-09-14 (DESCRIBE HISTORY; maintenance commits ignored).
* Declared constraints: none. Table comment is a generic dataset description; no column comments.
* Clustering / partitioning: none.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| franchiseID | bigint | 0.0 | 48 | 1.0 | key | primary key; range 3000000-3000047 |
| name | string | 0.0 | 46 | 0.9583 | dimension | store name; reference label (< 100 distinct, avg length 14.4); not unique |
| city | string | 0.0 | 47 | 0.9792 | dimension | store city; reference label (< 100 distinct, avg length 7.5) |
| district | string | 0.0 | 48 | 1.0 | dimension | store district / neighbourhood |
| zipcode | string | 0.0 | 48 | 1.0 | dimension | store postal code (business location) |
| country | string | 0.0 | 9 | 0.1875 | dimension | store country |
| size | string | 0.0 | 5 | 0.1042 | dimension | store size band |
| longitude | double | 0.0 | 48 | 1.0 | dimension | store longitude |
| latitude | double | 0.0 | 48 | 1.0 | dimension | store latitude |
| supplierID | bigint | 0.0 | 48 | 1.0 | fk | -> sales_suppliers.supplierID; unique per franchise |

## Value distributions
* `country`: Japan 20 (41.67%), US 16 (33.33%), Australia 6 (12.5%), France / Germany / Netherlands / Italy / Canada / Sweden 1 each (2.08%).
* `size`: S 10, M 10, XL 10, L 9, XXL 9.
* Cities per country: Japan 20 stores / 20 cities, US 16 / 15 (Seattle has 2 stores), Australia 6 / 6, other countries 1 / 1.
* `name`: 46 distinct across 48 stores; `Sugar Rush` and `Sweet Temptations` each name 2 stores.
* `longitude`: -157.8646 to 153.4276; `latitude`: -37.8005 to 59.3144.
* Transactions per franchise: 48-90 (avg 69.4); every franchise has transactions.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| franchiseID | referenced by samples.bakehouse.sales_transactions.franchiseID | 0.0 (unreferenced franchises: 0 of 48) | many_to_one (transactions -> franchises) |
| supplierID | samples.bakehouse.sales_suppliers.supplierID | 0.4375 (21 of 48 franchises) | one_to_one |

## Coded values
* `size`: `S` 10, `M` 10, `XL` 10, `L` 9, `XXL` 9. meaning: store size band (ordinal S < M < L < XL < XXL); exact definition not confirmed.
* `country`: 9 values (see distributions). Uses `US` where customers use `USA`.

## Lineage
upstream_tables: 0, downstream_tables: 129, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 3116, users_30d: 74. Common join/filter columns (sample of 20 distinct query shapes, 558 shapes overall): join `franchiseID` (15 shapes), `supplierID` (3 shapes); filter `country` (4 shapes).

## Data quality flags
* 21 of 48 franchises (supplierID 4000027-4000047) have no matching supplier row: suppliers only cover 4000000-4000026. Any franchise -> supplier join must be LEFT and supplier attributes will be null for 43.75% of franchises (1480 of 3333 transactions, 44.4%).
* `name` is not unique (2 names reused): group by `franchiseID` (or name + city) when a per-store figure is required.
* `country` value `US` vs customers' `USA`.

## Materialization signals
* `filter_columns`: `country` (categorical); also candidates `city`, `size`.
* `hot_table`: no (2nd by usage; cut-off is the top 1 of 4).
