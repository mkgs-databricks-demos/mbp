# Profile: samples.bakehouse.sales_suppliers

* Rows: 27 | Size: 4565 bytes | Files: 1 | Figures: exact
* Grain: one row per ingredient supplier | Primary key: `supplierID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: static content, periodically rebuilt by full replace: 50 `CREATE OR REPLACE TABLE AS SELECT` data commits between 2026-06-18 and 2026-09-14, last data write 2026-09-14 (DESCRIBE HISTORY; maintenance commits ignored).
* Declared constraints: none. Table comment is a generic dataset description; no column comments.
* Clustering / partitioning: none.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| supplierID | bigint | 0.0 | 27 | 1.0 | key | primary key; range 4000000-4000026 |
| name | string | 0.0 | 27 | 1.0 | dimension | supplier name; reference label (< 100 distinct, avg length 13.3) |
| ingredient | string | 0.0 | 27 | 1.0 | dimension | the single ingredient the supplier provides (one supplier per ingredient) |
| continent | string | 0.0 | 6 | 0.2222 | dimension | supplier continent |
| city | string | 0.0 | 27 | 1.0 | dimension | supplier city; reference label (< 100 distinct, avg length 7.3) |
| district | string | 0.0 | 27 | 1.0 | dimension | supplier district |
| size | string | 0.0 | 5 | 0.1852 | dimension | supplier size band |
| longitude | double | 0.0 | 27 | 1.0 | dimension | supplier longitude |
| latitude | double | 0.0 | 27 | 1.0 | dimension | supplier latitude |
| approved | string | 0.0 | 1 | 0.037 | dimension | approval flag; constant `Y` |

## Value distributions
* `continent`: Asia 11 (40.74%), Europe 5 (18.52%), South America 4 (14.81%), Africa 3 (11.11%), North America 3 (11.11%), Central America 1 (3.7%).
* `size`: M 7, S 7, XL 5, L 5, XXL 3.
* `approved`: Y 27 (100%).
* `ingredient`: 27 distinct (almonds, anise, cacao, cane sugar, cardamom, cashews, cinnamon, cloves, cocoa butter, coconut, coffee, fennel seeds, ginger, hazelnuts, honey, mace, maple syrup, molasses, nutmeg, oats, peanuts, pecans, pistachios, poppy seeds, raisins, sesame seeds, vanilla).
* `longitude`: -99.1332 to 128.1753; `latitude`: -23.5489 to 55.9533.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| supplierID | referenced by samples.bakehouse.sales_franchises.supplierID | 0.4375 on the franchise side (unreferenced suppliers: 0 of 27) | one_to_one (franchises -> suppliers) |

## Coded values
* `approved`: `Y` 27. meaning: approved supplier flag (not confirmed; no `N` value present).
* `size`: `M` 7, `S` 7, `XL` 5, `L` 5, `XXL` 3. meaning: supplier size band; definition not confirmed.
* `continent`: 6 values (see distributions).

## Lineage
upstream_tables: 0, downstream_tables: 39, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 2509, users_30d: 40. Common join/filter columns (sample of 20 distinct query shapes, 227 shapes overall): join `supplierID` (2 shapes); no filter column in 2+ shapes.

## Data quality flags
* `approved` is constant `Y`: no filtering value.
* Every supplier serves exactly one franchise, and 21 franchises have no supplier row (see sales_franchises profile).
* The data has no franchise-to-product or ingredient-to-product link: supplier/ingredient cannot be attributed to products sold.

## Materialization signals
none (27 rows; not in the top 1 of 4 by usage).
