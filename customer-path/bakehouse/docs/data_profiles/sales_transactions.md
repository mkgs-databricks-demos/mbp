# Profile: samples.bakehouse.sales_transactions

* Rows: 3333 | Size: 68624 bytes | Files: 1 | Figures: exact
* Grain: one row per sales transaction (single product line per transaction) | Primary key: `transactionID` (verified by pattern C: 0 duplicate keys) | Role: fact
* Update cadence: table is rebuilt by `CREATE OR REPLACE TABLE AS SELECT` about daily (median interval 1.0 day, max 4.0 days across 50 data commits in the last 100 history entries), last data write 2026-09-14 (DESCRIBE HISTORY). Content is static synthetic data: `dateTime` covers 2024-05-01 to 2024-05-17 only.
* No clustering or partition columns. No declared PK/FK constraints in `information_schema.table_constraints`.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| transactionID | bigint | 0.0 | 3333 | 1.0 | key | grain key |
| customerID | bigint | 0.0 | 300 | 0.09 | fk | -> sales_customers.customerID |
| franchiseID | bigint | 0.0 | 48 | 0.014 | fk | -> sales_franchises.franchiseID |
| dateTime | timestamp | 0.0 | 3333 | 1.0 | date | transaction timestamp |
| product | string | 0.0 | 6 | 0.002 | dimension | product name |
| quantity | bigint | 0.0 | 25 | 0.008 | measure | units sold, additive |
| unitPrice | bigint | 0.0 | 1 | 0.0003 | measure | constant 3 on every row; currency not stated |
| totalPrice | bigint | 0.0 | 25 | 0.008 | measure | revenue, additive; equals quantity * unitPrice on every row |
| paymentMethod | string | 0.0 | 3 | 0.0009 | dimension | card brand |
| cardNumber | bigint | 0.0 | 3333 | 1.0 | text | sensitive (values withheld): payment card number; treated as sensitive by judgment (`card` in name), unique per row, not a customer key |

## Value distributions
* `product` (6): Golden Gate Ginger 586 (17.58%), Tokyo Tidbits 583 (17.49%), Outback Oatmeal 561 (16.83%), Pearly Pies 550 (16.5%), Austin Almond Biscotti 530 (15.9%), Orchard Oasis 523 (15.69%).
* `paymentMethod` (3): mastercard 1144 (34.32%), amex 1106 (33.18%), visa 1083 (32.49%).
* `quantity`: min 1, max 60, avg 6.65. 1-10 cover 3094 rows (92.8%); larger quantities are multiples (12, 14, 16, 18, 20, 24, 28, 30, 32, 36, 40, 42, 48, 54, 60).
* `unitPrice`: min 3, max 3 (constant).
* `totalPrice`: min 3, max 180, avg 19.94; sum = 3 * sum(quantity).
* `dateTime`: min 2024-05-01 00:03:28, max 2024-05-17 11:48:38. 181-229 transactions per full day; 2024-05-17 is a partial day (106).
* Per customer: 3-22 transactions (avg 11.11). Per franchise: 48-90 transactions (avg 69.44).

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| customerID | samples.bakehouse.sales_customers.customerID | 0.0 | many_to_one |
| franchiseID | samples.bakehouse.sales_franchises.franchiseID | 0.0 | many_to_one |

## Coded values
* `paymentMethod`: `mastercard` 1144, `amex` 1106, `visa` 1083. Meaning: card brand (values are self-describing brand names).
* `product`: 6 values listed above. Meaning: product name (self-describing).

## Lineage
upstream_tables: 0, downstream_tables: 124, entity_types: 5, last_seen: 2026-11-27 (system.access.table_lineage, last 90 days; counts only).

## Usage
queries_30d: 3762, users_30d: 82 (system.query.history, word-boundary `rlike`). Common join/filter columns: none appear in `JOIN ... ON` or `WHERE` in 2+ of the 6 distinct query shapes in the 20-statement sample.

## Data quality flags
* `unitPrice` is constant (3) and currency is not stated; Average Unit Price is always 3.
* `dateTime` covers 17 days (one partial); year-over-year, same-store growth and multi-period retention cannot be computed beyond day/week windows inside May 2024.
* `cardNumber` is unique per row: it cannot identify repeat payers.
* No nulls, no duplicate keys, no orphan foreign keys.

## Materialization signals
* `hot_table`: highest `queries_30d` of the 4 source tables (top ceil(4/4) = 1).
* `fan_out`: customer and franchise attributes read through this fact must count distinct `customerID` / `franchiseID`.
* `multi_join`: supplier KPIs over sales (Supplier Concentration by franchise sales) need transactions -> franchises -> suppliers (3 tables).
* `large_table`: no (3333 rows).
* Candidate dimensions: `product`, `paymentMethod`, date of `dateTime`.
