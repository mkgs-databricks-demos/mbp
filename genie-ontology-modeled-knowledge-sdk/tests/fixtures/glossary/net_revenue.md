---
term: Net Revenue
synonyms: [net sales, discounted revenue, Net Revenue]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Discount, Gross Revenue]
sources:
  - https://www.tpc.org/tpch/
---

## Definition

Revenue after line item discounts, before tax. Computed per line item as extended price times one minus discount.

## Business context

The primary sales KPI in TPC-H query Q5 and Q10.

## Data usage

`SUM(l_extendedprice * (1 - l_discount))` over `lineitem`.
