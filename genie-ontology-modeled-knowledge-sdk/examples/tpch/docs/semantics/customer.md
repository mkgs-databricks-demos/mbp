---
term: Customer
synonyms: [buyer, account, c_custkey]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Market Segment, Order Volume, Revenue]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf
---

## Definition
A party that places orders with the wholesale supplier. CUSTOMER is one of the eight TPC-H tables, linked to ORDERS and to NATION ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)).

## Business context
The unit for customer analysis: revenue by customer, segment and nation. TPC-H Q10 ranks customers by revenue lost on returned items ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
`samples.tpch.customer`, key `c_custkey`. Join orders on `o_custkey = c_custkey` and nation on `c_nationkey = n_nationkey`. Attributes: `c_mktsegment`, `c_acctbal`. Name, address and phone are synthetic (see `docs/research/03_regulatory_context.md`).
