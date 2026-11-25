---
term: Return Flag
synonyms: [l_returnflag, returned indicator]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [Return Rate, Line Item, Gross Charge]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
A one-character code on each line item that indicates its return status. `l_returnflag` is fixed text of size 1 ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)), and TPC-H Q10 selects returned items with `l_returnflag = 'R'` ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Q1 (pricing summary) groups by return flag and line status, and Q10 uses it to find revenue lost on returns ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
Dimension `samples.tpch.lineitem.l_returnflag`. `'R'` = returned. The meanings of the other values were not confirmed by a source in this session; session 10b's EDA should list the distinct values.
