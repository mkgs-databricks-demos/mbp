---
term: Supplier
synonyms: [vendor, s_suppkey]
domain: tpch_supply_chain
subdomain: procurement
related_terms: [Part, Supply Cost, Inventory Value, National Market Share]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf
---

## Definition
A company that supplies parts to the wholesaler. SUPPLIER is one of the eight TPC-H tables, linked to PARTSUPP and to NATION ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)).

## Business context
Supplier nation drives TPC-H market share (Q8) and profit (Q9), and Q11 values each supplier's stock ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Procurement uses it to compare sourcing by nation.

## Data usage
`samples.tpch.supplier`, key `s_suppkey`. Join `partsupp` on `ps_suppkey`, `lineitem` on `l_suppkey` and nation on `s_nationkey = n_nationkey`. Attribute: `s_acctbal`.
