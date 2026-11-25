---
term: Revenue
synonyms: [net revenue, discounted revenue, sum_disc_price, volume]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Extended Price, Gross Charge, Discount Revenue, National Market Share, Average Order Value, Profit]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The discounted price of line items, `l_extendedprice * (1 - l_discount)`. TPC-H Q1 calls it `sum_disc_price` and Q5 calls it `revenue` ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
The main sales measure. Q5 (local supplier volume) and Q8 (national market share) both build on it ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Sales and pricing teams use it to compare nations, regions, segments and periods.

## Data usage
`sum(l_extendedprice * (1 - l_discount))` over `samples.tpch.lineitem`. Grain: line item. Join `orders` on `l_orderkey = o_orderkey` for order date, customer and priority. Excludes tax; see Gross Charge for the taxed amount. Do not multiply by `l_quantity`, because `l_extendedprice` already includes it.
