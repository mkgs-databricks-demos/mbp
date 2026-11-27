# Profile: samples.bakehouse.sales_franchises

* Rows: 48 | Size: 5472 bytes | Files: 1 | Figures: exact
* Grain: one row per franchise store | Primary key: `franchiseID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: rebuilt by `CREATE OR REPLACE TABLE AS SELECT` about daily (50 data commits in the last 100 history entries, 2026-06-18 to 2026-09-14), last data write 2026-09-14 (DESCRIBE HISTORY). Content is static synthetic data.
* No clustering or partition columns. No declared PK/FK constraints.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| franchiseID | bigint | 0.0 | 48 | 1.0 | key | grain key |
| name | string | 0.0 | 46 | 0.96 | dimension | store name; reference label (< 100 distinct, avg length 14.4); not unique |
| city | string | 0.0 | 47 | 0.98 | dimension | store city; reference label (< 100 distinct, avg length 7.5) |
| district | string | 0.0 | 48 | 1.0 | dimension | neighbourhood of the store |
| zipcode | string | 0.0 | 48 | 1.0 | text | store postal code (string; mixed formats by country) |
| country | string | 0.0 | 9 | 0.19 | dimension | store country |
| size | string | 0.0 | 5 | 0.10 | dimension | store size code |
| longitude | double | 0.0 | 48 | 1.0 | dimension | store location |
| latitude | double | 0.0 | 48 | 1.0 | dimension | store location |
| supplierID | bigint | 0.0 | 48 | 1.0 | fk | -> sales_suppliers.supplierID (43.75% orphans) |

## Value distributions
* `country` (9): Japan 20 (41.67%), US 16 (33.33%), Australia 6 (12.5%), France 1, Germany 1, Netherlands 1, Italy 1, Canada 1, Sweden 1.
* `size` (5): S 10, M 10, XL 10, L 9, XXL 9.
* `name` (46): every name once except `Sugar Rush` (2) and `Sweet Temptations` (2).
* `city` (47): every city once except `Seattle` (2).
* `longitude`: min -157.8646, max 153.4276. `latitude`: min -37.8005, max 59.3144.
* `supplierID`: 4000000-4000047, one distinct supplier per franchise.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| franchiseID | referenced by samples.bakehouse.sales_transactions.franchiseID (fact -> this table) | 0.0 (unreferenced_rate 0.0) | many_to_one |
| supplierID | samples.bakehouse.sales_suppliers.supplierID | 0.4375 (21 of 48) | one_to_one |

## Coded values
* `size`: `S` 10, `M` 10, `XL` 10, `L` 9, `XXL` 9. meaning: not confirmed (likely store size class S..XXL).
* `country`: 9 values above. Note `US` here vs `USA` in sales_customers.

## Lineage
upstream_tables: 0, downstream_tables: 129, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 3127, users_30d: 74. Common join/filter columns (8 distinct query shapes in the 20-statement sample): join `franchiseID` (5 shapes); filter `name` (2 shapes).

## Data quality flags
* 21 of 48 franchises (43.75%) reference a `supplierID` (4000027-4000047) that does not exist in sales_suppliers. Supplier attributes are NULL for these franchises under a LEFT join; an INNER join drops them.
* `name` is not unique (2 names used twice): group and count by `franchiseID`, display `name`.
* `city` is not unique (`Seattle` twice).
* Every franchise has transactions (unreferenced_rate 0.0).

## Materialization signals
* `fan_out`: dimension reached from sales_transactions; franchise counts through the fact need count(DISTINCT franchiseID).
* `multi_join`: on the transactions -> franchises -> suppliers path.
* `filter_columns`: `name` (categorical, 46 values).
* Candidate dimensions: `country`, `city`, `size`, `name`.
