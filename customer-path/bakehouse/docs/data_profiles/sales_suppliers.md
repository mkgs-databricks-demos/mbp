# Profile: samples.bakehouse.sales_suppliers

* Rows: 27 | Size: 4565 bytes | Files: 1 | Figures: exact
* Grain: one row per ingredient supplier | Primary key: `supplierID` (verified by pattern C: 0 duplicate keys) | Role: dimension
* Update cadence: rebuilt by `CREATE OR REPLACE TABLE AS SELECT` about daily (50 data commits in the last 100 history entries, 2026-06-18 to 2026-09-14), last data write 2026-09-14 (DESCRIBE HISTORY). Content is static synthetic data.
* No clustering or partition columns. No declared PK/FK constraints.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| supplierID | bigint | 0.0 | 27 | 1.0 | key | grain key (4000000-4000026) |
| name | string | 0.0 | 27 | 1.0 | dimension | supplier name; reference label (< 100 distinct, avg length 13.3) |
| ingredient | string | 0.0 | 27 | 1.0 | dimension | one ingredient per supplier |
| continent | string | 0.0 | 6 | 0.22 | dimension | supplier continent |
| city | string | 0.0 | 27 | 1.0 | dimension | supplier city; reference label (< 100 distinct, avg length 7.3) |
| district | string | 0.0 | 27 | 1.0 | dimension | supplier neighbourhood |
| size | string | 0.0 | 5 | 0.19 | dimension | supplier size code |
| longitude | double | 0.0 | 27 | 1.0 | dimension | supplier location |
| latitude | double | 0.0 | 27 | 1.0 | dimension | supplier location |
| approved | string | 0.0 | 1 | 0.04 | dimension | constant `Y` |

## Value distributions
* `continent` (6): Asia 11 (40.74%), Europe 5 (18.52%), South America 4 (14.81%), Africa 3 (11.11%), North America 3 (11.11%), Central America 1 (3.7%).
* `size` (5): M 7, S 7, XL 5, L 5, XXL 3.
* `approved` (1): Y 27 (100%).
* `ingredient` (27, all distinct), e.g. raisins, ginger, sesame seeds, peanuts, pistachios, coffee, maple syrup, honey, cashews, cinnamon, coconut, pecans, vanilla, oats, cacao, hazelnuts, cane sugar, molasses, almonds, cardamom.
* `longitude`: min -99.1332, max 128.1753. `latitude`: min -23.5489, max 55.9533.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| supplierID | referenced by samples.bakehouse.sales_franchises.supplierID (franchises -> this table) | 0.4375 on the franchise side; unreferenced_rate 0.0 | one_to_one |

## Coded values
* `approved`: `Y` 27. meaning: not confirmed (likely approved = yes); no other value is observed, so the flag does not discriminate.
* `size`: `M` 7, `S` 7, `XL` 5, `L` 5, `XXL` 3. meaning: not confirmed (likely supplier size class).
* `continent`: 6 values above.

## Lineage
upstream_tables: 0, downstream_tables: 39, entity_types: 5, last_seen: 2026-11-27 (counts only).

## Usage
queries_30d: 2513, users_30d: 40. Common join/filter columns (11 distinct query shapes in the 20-statement sample): join `supplierID` (2 shapes); no filter column in 2+ shapes.

## Data quality flags
* `approved` is constant `Y`: Approved Supplier Rate over franchises is driven only by the 21 franchises whose supplier is missing from this table (27/48 = 56.25% if missing suppliers count as not approved; 100% over matched franchises).
* Every supplier serves exactly one franchise (no supplier is shared), so Supplier Concentration over franchises is flat (1 franchise each).
* Every supplier is referenced (unreferenced_rate 0.0).

## Materialization signals
* `multi_join`: supplier KPIs over sales need transactions -> franchises -> suppliers.
* Candidate dimensions: `continent`, `ingredient`, `size`, `name`.
