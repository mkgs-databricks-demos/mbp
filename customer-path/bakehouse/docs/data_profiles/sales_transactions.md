# Profile: samples.bakehouse.sales_transactions

* Rows: 3333 | Size: 68624 bytes | Files: 1 | Figures: exact
* Grain: one row per point-of-sale transaction (one product line per transaction) | Primary key: `transactionID` (verified by pattern C: 0 duplicate keys) | Role: fact
* Update cadence: static content, periodically rebuilt by full replace: 50 `CREATE OR REPLACE TABLE AS SELECT` data commits between 2026-06-18 and 2026-09-14 (about every 1.8 days), last data write 2026-09-14 (DESCRIBE HISTORY; `SET TBLPROPERTIES` maintenance commits ignored). Event dates in the data do not move with rebuilds.
* Declared constraints: none (`samples.information_schema.table_constraints` is empty for `bakehouse`). Table comment is a generic dataset description; no column comments.
* Clustering / partitioning: none.

## Columns
| column | type | null_rate | distinct | uniqueness_ratio | role (key, fk, measure, dimension, date, text) | comment |
|---|---|---|---|---|---|---|
| transactionID | bigint | 0.0 | 3333 | 1.0 | key | primary key; range 1000000-1003332 (contiguous) |
| customerID | bigint | 0.0 | 300 | 0.09 | fk | -> sales_customers.customerID |
| franchiseID | bigint | 0.0 | 48 | 0.0144 | fk | -> sales_franchises.franchiseID |
| dateTime | timestamp | 0.0 | 3333 | 1.0 | date | transaction timestamp |
| product | string | 0.0 | 6 | 0.0018 | dimension | product name (avg length 15.3) |
| quantity | bigint | 0.0 | 25 | 0.0075 | measure | units sold |
| unitPrice | bigint | 0.0 | 1 | 0.0003 | measure | constant 3 in every row |
| totalPrice | bigint | 0.0 | 25 | 0.0075 | measure | revenue; always equals quantity * unitPrice |
| paymentMethod | string | 0.0 | 3 | 0.0009 | dimension | card network |
| cardNumber | bigint | 0.0 | 3333 | 1.0 | text | sensitive (values withheld) - token `card`; unique per row, not a customer-level key |

## Value distributions
* `product` (6 values): Golden Gate Ginger 586 (17.58%), Tokyo Tidbits 583 (17.49%), Outback Oatmeal 561 (16.83%), Pearly Pies 550 (16.50%), Austin Almond Biscotti 530 (15.90%), Orchard Oasis 523 (15.69%).
* `paymentMethod` (3 values): mastercard 1144 (34.32%), amex 1106 (33.18%), visa 1083 (32.49%).
* `unitPrice`: 3 in 100% of rows.
* `quantity`: min 1, max 60, avg 6.65. Values 1-10 cover ~93% of rows (1 is the most common at 13.38%); a long tail of larger multiples (12, 14, 16, 18, 20, 24, 36, 40, 54, 60, ...).
* `totalPrice`: min 3, max 180, avg 19.94, sum 66471. Distribution mirrors `quantity` x 3.
* `dateTime`: min 2024-05-01 00:03:28, max 2024-05-17 11:48:38; 17 distinct days, 181-229 transactions per full day; 2024-05-17 is a partial day (106 rows, ends 11:48).
* Transactions per franchise: min 48, max 90, avg 69.4. Transactions per customer: min 3, max 22, avg 11.1. One customer buys at up to 18 different franchises.

## Keys and joins
| column | references | orphan_rate | verified_cardinality |
|---|---|---|---|
| customerID | samples.bakehouse.sales_customers.customerID | 0.0 | many_to_one |
| franchiseID | samples.bakehouse.sales_franchises.franchiseID | 0.0 | many_to_one |

## Coded values
* `paymentMethod`: `mastercard` 1144, `amex` 1106, `visa` 1083. Meaning: card network (self-describing values).
* `product`: 6 product names (see distributions). meaning: not confirmed beyond the name.
* `unitPrice`: single value `3`; currency not stated in the data (meaning: not confirmed).

## Lineage
upstream_tables: 0, downstream_tables: 124, entity_types: 5, last_seen: 2026-11-27 (system.access.table_lineage, last 90 days; counts only).

## Usage
queries_30d: 3733, users_30d: 82 (system.query.history, word-boundary match). Common join/filter columns (sample of 20 distinct query shapes with JOIN or WHERE, 749 shapes overall): join `franchiseID` (13 shapes), `product` (3 shapes); filter `dateTime` (13 shapes).

## Data quality flags
* `unitPrice` is constant (3): price variation measures (avg unit price by product) carry no signal; revenue is effectively `3 * quantity`.
* `dateTime` covers only 2024-05-01 to 2024-05-17 and the last day is partial: daily trends should exclude or flag 2024-05-17; month-level grains have a single (partial) month.
* `cardNumber` is unique per transaction, so it cannot identify repeat payers; treat as sensitive and do not expose as a dimension.
* No nulls, no duplicate keys, no orphans.

## Materialization signals
* `hot_table`: top source table by `queries_30d` (3733 of 4 tables; cut-off ceil(4/4) = 1).
* `filter_columns`: `dateTime` (time dimension; derive date/day grain), categorical candidates `product`, `paymentMethod`.
* `multi_join` (pending): supplier coverage in `domain_context` needs transactions -> franchises -> suppliers (3 tables); `docs/research/02_kpi_definitions.md` was empty at profiling time, so not confirmed against KPI definitions.
* `large_table`: no (3333 rows).
