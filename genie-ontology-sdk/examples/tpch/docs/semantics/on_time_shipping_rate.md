---
term: On-Time Shipping Rate
synonyms: [on-time delivery rate, delivery performance, OTD]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [Late Receipt, Perfect Order Rate, Line Item, Ship Mode]
sources:
  - https://scor.ascm.org/performance/reliability/RL.3.1
  - https://scor.ascm.org/performance/reliability/RL.1.1
  - https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/
---

## Definition
The share of orders delivered on time. SCOR defines delivery performance as orders delivered in full and on time to the customer's request date divided by total orders delivered, times 100% ([SCOR Model RL.3.1](https://scor.ascm.org/performance/reliability/RL.3.1)). SCOR ties "on time" to the customer commit or request date ([SCOR Model RL.1.1](https://scor.ascm.org/performance/reliability/RL.1.1)).

## Business context
The headline reliability KPI for distributors. NAW / MDM reports an average of 85-90% for mid-market distributors and 95-98% for best in class ([NAW](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/)). TPC-H data is synthetic, so treat these as context, not targets.

## Data usage
Ship-based proxy (seed definition): `avg(case when l_shipdate <= l_commitdate then 1 else 0 end)` over `samples.tpch.lineitem`. Delivery-based alternative: `l_receiptdate <= l_commitdate`. Grain: line item. An order-level rate needs every line of the order on time. The owner picks the basis (see `docs/research/02_kpi_definitions.md`).
