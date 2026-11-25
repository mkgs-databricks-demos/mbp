---
term: Market Segment
synonyms: [c_mktsegment, customer segment]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Customer, Revenue, Order Volume]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
The industry segment a customer belongs to. The benchmark uses five segments: AUTOMOBILE, BUILDING, FURNITURE, MACHINERY and HOUSEHOLD ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
The main way to segment customers for sales analysis. TPC-H queries use it as a substitution parameter to filter orders by segment ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Data usage
Dimension `samples.tpch.customer.c_mktsegment`. Join to orders on `o_custkey = c_custkey`. Session 10b's EDA should confirm the distinct values in `samples.tpch`.
