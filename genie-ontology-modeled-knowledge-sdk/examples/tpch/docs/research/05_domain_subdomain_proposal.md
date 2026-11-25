# 05 Domain / Subdomain Proposal — tpch_supply_chain

## Proposed domain
* Name: tpch_supply_chain
* Description: A worldwide wholesale supplier's sales, order fulfillment and procurement, as modeled by the TPC-H benchmark ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)).

## Subdomains
| subdomain | description | source tables | candidate metric views | glossary terms |
|---|---|---|---|---|
| sales | Customers, orders, pricing, revenue and market share by nation and region | samples.tpch.customer, samples.tpch.orders, samples.tpch.nation, samples.tpch.region | mv_tpch_supply_chain_revenue, mv_tpch_supply_chain_orders, mv_tpch_supply_chain_market_share | Revenue, Gross Charge, Discount Revenue, Extended Price, Order Volume, Average Order Value, National Market Share, Market Segment, Order Priority, Customer |
| fulfillment | Line-item shipping, delivery timing, ship modes and returns | samples.tpch.lineitem | mv_tpch_supply_chain_fulfillment, mv_tpch_supply_chain_returns | Line Item, On-Time Shipping Rate, Late Receipt, Order Fulfillment Cycle Time, Perfect Order Rate, Return Rate, Return Flag, Ship Mode |
| procurement | Parts, suppliers, supply cost, available stock and profit | samples.tpch.part, samples.tpch.partsupp, samples.tpch.supplier | mv_tpch_supply_chain_supply_cost, mv_tpch_supply_chain_profit | Part, Supplier, Supply Cost, Inventory Value, Profit |

## Rationale
* The split follows the business areas of the TPC-H queries: pricing, revenue and market share (Q1, Q5, Q6, Q8), shipping and returns (Q10, Q12), and stock and profit (Q9, Q11) ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf); see [02_kpi_definitions.md](02_kpi_definitions.md)).
* `lineitem` is the fact table for both revenue and fulfillment. It is assigned to `fulfillment` because its own columns are mostly shipping and return attributes; the sales revenue metric views still join to it. Glossary terms are assigned by business meaning, so Revenue is in `sales` although its formula reads `lineitem`.
* `nation` and `region` are shared dimensions (customers and suppliers both reference nation, per [TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)). They are assigned to `sales` because market share by nation is a sales analysis; procurement views join them too.
* Seven candidate metric views across three subdomains: no subdomain is close to `max_metric_views_per_agent` (50, from `sdk_config.json`).

## Alternatives considered
* A single subdomain for all eight tables: simpler, but it hides the sales / fulfillment / procurement split that later agent curation can use. Rejected because the KPI set clearly separates into three areas.
* A fourth `geography` subdomain for `nation` and `region`: rejected because it would hold no metrics of its own, only dimensions.

## Owner decisions needed
* [ ] Create the domain and subdomains in UC (opt-in)
* [ ] Confirm `lineitem` in `fulfillment` (alternative: `sales`)
* [ ] Confirm `nation` / `region` in `sales`

## Sources
1. [TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf) — Transaction Processing Performance Council
2. [TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf) — Transaction Processing Performance Council
