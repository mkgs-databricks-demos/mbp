# 02 KPI Definitions — tpch_supply_chain

## Summary
The TPC-H business queries define the domain's core pricing, revenue, market share, profit and inventory formulas directly in terms of the source columns ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Operational fulfillment KPIs (delivery performance, perfect order, cycle time, return rate) come from the ASCM SCOR model ([SCOR Model RL.1.1](https://scor.ascm.org/performance/reliability/RL.1.1)). Where a SCOR KPI has no exact column equivalent, the mapping below is marked as a proxy. Average order value is a common commerce KPI, not a SCOR metric (see Open questions).

## Findings

### KPI table
| kpi | formula | numerator | denominator | grain | time_period | source | candidate_tables |
|---|---|---|---|---|---|---|---|
| Revenue (discounted price) | `sum(l_extendedprice * (1 - l_discount))` | discounted extended price | — | line item | any (Q5 uses one order year) | [TPC-H v2.18.0 Q1, Q5](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem, orders |
| Gross charge (with tax) | `sum(l_extendedprice * (1 - l_discount) * (1 + l_tax))` | charged amount | — | line item | ship date cutoff (Q1) | [TPC-H v2.18.0 Q1](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem |
| Discount revenue (forecast revenue change) | `sum(l_extendedprice * l_discount)` | discount amount | — | line item | one ship year (Q6) | [TPC-H v2.18.0 Q6](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem |
| National market share | `sum(case when nation = :nation then volume else 0 end) / sum(volume)`, `volume = l_extendedprice * (1 - l_discount)` | volume from the given supplier nation | total volume | line item, by order year | 1995-1996 (Q8) | [TPC-H v2.18.0 Q8](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem, orders, part, supplier, customer, nation, region |
| Product type profit | `sum(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity)` | profit amount | — | line item, by nation and year | all years (Q9) | [TPC-H v2.17.3 Q9](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf) | lineitem, partsupp, part, supplier, orders, nation |
| Inventory value (important stock) | `sum(ps_supplycost * ps_availqty)` | stock value | — | part-supplier | snapshot (Q11) | [TPC-H v2.18.0 Q11](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | partsupp, supplier, nation |
| Returned item revenue lost | `sum(l_extendedprice * (1 - l_discount)) where l_returnflag = 'R'` | revenue on returned line items | — | line item, by customer | one quarter (Q10) | [TPC-H v2.18.0 Q10](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem, orders, customer, nation |
| Late receipt by priority | `sum(case when o_orderpriority in ('1-URGENT','2-HIGH') then 1 else 0 end)` (and the complement) over line items with `l_commitdate < l_receiptdate` and `l_shipdate < l_commitdate` | high (or low) priority late line items | — | line item, by ship mode | one receipt year (Q12) | [TPC-H v2.18.0 Q12](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) | lineitem, orders |
| Delivery performance (on-time rate) | `orders delivered in full and on time to the customer's request date / total orders delivered x 100%` | on-time, in-full orders | delivered orders | order | any | [SCOR Model RL.3.1](https://scor.ascm.org/performance/reliability/RL.3.1) | lineitem (proxy: `l_receiptdate <= l_commitdate`, or `l_shipdate <= l_commitdate` for on-time shipping) |
| Perfect order fulfillment | `total perfect orders / total orders x 100%` | perfect orders | all orders | order | any | [SCOR Model RL.1.1](https://scor.ascm.org/performance/reliability/RL.1.1) | not fully mappable (no damage or documentation data); partial proxy from lineitem |
| Order fulfillment cycle time | elapsed time from order receipt to fulfillment (SCOR gives a definition, no single formula) | — | — | order | any | [SCOR Model RS.3.111](https://scor.ascm.org/performance/responsiveness/RS.3.111) | orders, lineitem (proxy: `l_receiptdate - o_orderdate`) |
| Return rate | `weight of products returned / weight of products shipped x 100%` | returned weight | shipped weight | product | any | [SCOR Model AM.3.8](https://scor.ascm.org/performance/assets/AM.3.8) | lineitem (proxy: quantity or line count with `l_returnflag = 'R'` over all; no weight column) |
| Order volume | `count(distinct o_orderkey)` | — | — | order | any | not found (count of orders; no external formula sourced) | orders |
| Average order value | `total revenue / number of orders` (common usage; not a SCOR metric) | revenue | orders | order | any | not found as a standard; see Open questions | orders, lineitem |

### Notes
* `l_extendedprice` is already `l_quantity * p_retailprice`, so revenue formulas must not multiply by quantity again ([TPC-H v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).
* SCOR's formal on-time metric is tied to the customer commit or request date ([SCOR Model RL.1.1](https://scor.ascm.org/performance/reliability/RL.1.1)); in TPC-H the commit date is `l_commitdate`.
* SCOR measures responsiveness with Order Fulfillment Cycle Time ([SCOR Model Introduction](https://scor.ascm.org/performance/introduction)).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Revenue, gross charge, discount revenue | `lineitem.l_extendedprice`, `l_discount`, `l_tax` | measures |
| Market share, profit by nation | `nation.n_name`, `region.r_name`, `supplier.s_nationkey`, `customer.c_nationkey` | dimensions |
| Profit, inventory value | `partsupp.ps_supplycost`, `ps_availqty`, `lineitem.l_quantity` | measures |
| On-time, late receipt, cycle time | `lineitem.l_shipdate`, `l_commitdate`, `l_receiptdate`, `orders.o_orderdate` | measures, filters |
| Returns | `lineitem.l_returnflag` | filter, measure |
| Priority and ship mode | `orders.o_orderpriority`, `lineitem.l_shipmode` | dimensions |

## Open questions
* Average order value: use `o_totalprice` (order header total) or the sum of line-item revenue? The owner must choose; they differ by discounts and tax.
* On-time: ship-based (`l_shipdate <= l_commitdate`) or receipt-based (`l_receiptdate <= l_commitdate`)? The seed list says ship date; SCOR is delivery based.
* Return rate: line count, quantity or revenue basis (no weight column exists).

## Sources
1. [TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) — Transaction Processing Performance Council
2. [TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf) — Transaction Processing Performance Council
3. [SCOR Model RL.1.1 Perfect Customer Order Fulfillment](https://scor.ascm.org/performance/reliability/RL.1.1) — ASCM
4. [SCOR Model RL.3.1](https://scor.ascm.org/performance/reliability/RL.3.1) — ASCM
5. [SCOR Model RS.3.111](https://scor.ascm.org/performance/responsiveness/RS.3.111) — ASCM
6. [SCOR Model AM.3.8](https://scor.ascm.org/performance/assets/AM.3.8) — ASCM
7. [SCOR Model Introduction](https://scor.ascm.org/performance/introduction) — ASCM
