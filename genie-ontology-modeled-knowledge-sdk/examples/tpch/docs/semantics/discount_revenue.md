---
term: Discount Revenue
synonyms: [discount amount, forecast revenue change, revenue given away by discounts]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Revenue, Extended Price]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The revenue given up through discounts, `l_extendedprice * l_discount`. TPC-H Q6 (forecasting revenue change) defines it as the potential revenue increase if discounts in a given range were removed ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Pricing teams use it to judge what a discount program costs and to decide whether to remove small discounts ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
`sum(l_extendedprice * l_discount)` over `samples.tpch.lineitem`. Grain: line item. Q6 filters to one ship year (`l_shipdate`), a discount range (`l_discount`) and a quantity limit (`l_quantity`).
