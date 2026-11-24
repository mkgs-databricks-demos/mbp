---
term: Order Fulfillment Cycle Time
synonyms: [order cycle time, lead time, OFCT]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [On-Time Shipping Rate, Late Receipt, Line Item]
sources:
  - https://scor.ascm.org/performance/introduction
  - https://scor.ascm.org/performance/responsiveness/RS.3.111
---

## Definition
The elapsed time to fulfill a customer order, from order processing through pick, ship and transit. SCOR uses Order Fulfillment Cycle Time as its responsiveness KPI ([SCOR Model Introduction](https://scor.ascm.org/performance/introduction)) and lists these process steps in its definition ([SCOR Model RS.3.111](https://scor.ascm.org/performance/responsiveness/RS.3.111)). The retrieved SCOR pages give no single formula.

## Business context
Measures how fast the supplier responds to demand. It complements on-time rate, which only says whether the commit date was met.

## Data usage
Proxy: `datediff(l_receiptdate, o_orderdate)` in days, per line item, joining `samples.tpch.lineitem` to `samples.tpch.orders` on `l_orderkey = o_orderkey`. Order level: `max` over the order's lines. Ship lead time (`datediff(l_shipdate, o_orderdate)`) is a narrower variant.
