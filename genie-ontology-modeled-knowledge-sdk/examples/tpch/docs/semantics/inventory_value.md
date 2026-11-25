---
term: Inventory Value
synonyms: [stock value, important stock value, available stock value]
domain: tpch_supply_chain
subdomain: procurement
related_terms: [Supply Cost, Supplier, Part]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The cost value of available stock, `sum(ps_supplycost * ps_availqty)`. TPC-H Q11 (important stock identification) computes it per part and keeps parts above a fraction of the total ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Q11 finds the parts that make up a large share of stock value for suppliers in a given nation ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Procurement and inventory planners use it to focus on high-value stock.

## Data usage
`sum(ps_supplycost * ps_availqty)` over `samples.tpch.partsupp`, grouped by `ps_partkey`. Join `supplier` on `ps_suppkey` and `nation` on `s_nationkey` for the nation filter. Snapshot measure: no date column.
