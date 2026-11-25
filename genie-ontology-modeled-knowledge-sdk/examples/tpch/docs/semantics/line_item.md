---
term: Line Item
synonyms: [order line, lineitem]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [Extended Price, Revenue, Return Flag, Ship Mode, On-Time Shipping Rate]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf
---

## Definition
One line of an order: a quantity of one part from one supplier, with its price, discount, tax, ship, commit and receipt dates, ship mode, return flag and line status. LINEITEM is the TPC-H table linked to ORDERS ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)).

## Business context
The fact grain for almost every TPC-H KPI: revenue, discounts, on-time, returns and profit ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
`samples.tpch.lineitem`. Key `(l_orderkey, l_linenumber)`. Join `orders` on `l_orderkey = o_orderkey`, `partsupp` on `(l_partkey, l_suppkey) = (ps_partkey, ps_suppkey)`, `part` on `l_partkey`, `supplier` on `l_suppkey`. Session 10b verifies key uniqueness and join cardinality.
