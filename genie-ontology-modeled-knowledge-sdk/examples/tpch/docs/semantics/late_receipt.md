---
term: Late Receipt
synonyms: [late delivery, received after commit date]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [On-Time Shipping Rate, Order Priority, Ship Mode]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
A line item the customer received after its committed date (`l_commitdate < l_receiptdate`). TPC-H Q12 counts these for line items that also shipped before the commit date (`l_shipdate < l_commitdate`) ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Q12 uses late receipts by ship mode and order priority to judge whether cheaper ship modes delay critical orders ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
Flag: `l_receiptdate > l_commitdate` on `samples.tpch.lineitem`. Q12 version adds `l_shipdate < l_commitdate` and filters one receipt year and two ship modes. Count: `sum(case when l_receiptdate > l_commitdate then 1 else 0 end)`.
