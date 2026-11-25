---
term: Supply Cost
synonyms: [ps_supplycost, supplier cost, unit cost]
domain: tpch_supply_chain
subdomain: procurement
related_terms: [Profit, Inventory Value, Part, Supplier]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/tpc-r_v2.1.0.pdf
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
The supplier's cost for one unit of a part, stored on the part-supplier pairing (`ps_supplycost`) ([TPC-R Specification v2.1.0](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/tpc-r_v2.1.0.pdf)).

## Business context
The cost side of profit: TPC-H Q9 subtracts `ps_supplycost * l_quantity` from revenue ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)). Procurement compares it across suppliers for the same part.

## Data usage
`samples.tpch.partsupp.ps_supplycost`, keyed by `(ps_partkey, ps_suppkey)`. Cost of goods for line items: `sum(ps_supplycost * l_quantity)`, joining `lineitem` on `(l_partkey, l_suppkey)`. Average unit cost: `avg(ps_supplycost)`.
