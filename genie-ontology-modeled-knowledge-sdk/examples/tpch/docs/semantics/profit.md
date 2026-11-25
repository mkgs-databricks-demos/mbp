---
term: Profit
synonyms: [product type profit, gross profit, amount]
domain: tpch_supply_chain
subdomain: procurement
related_terms: [Revenue, Supply Cost, Part, Supplier]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
Revenue minus supply cost per line item, `l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity`. TPC-H Q9 (product type profit measure) sums it by nation and year ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
Shows which supplier nations and part lines make money, and how that changes by year ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Data usage
`sum(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity)`. Join `samples.tpch.lineitem` to `partsupp` on `(l_partkey, l_suppkey) = (ps_partkey, ps_suppkey)`, `supplier` -> `nation` (group by `n_name`), `orders` (`year(o_orderdate)`) and `part` (name filter). Grain: line item.
