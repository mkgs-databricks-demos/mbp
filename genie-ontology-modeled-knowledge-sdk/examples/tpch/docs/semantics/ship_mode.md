---
term: Ship Mode
synonyms: [l_shipmode, shipping mode, transport mode]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [Late Receipt, Order Priority, On-Time Shipping Rate]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The transport method for a line item, for example AIR, RAIL, SHIP, TRUCK or MAIL. `l_shipmode` is fixed text of size 10 ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
TPC-H Q12 compares late receipts across two ship modes, split by order priority ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Logistics teams use it to trade cost against speed.

## Data usage
Dimension `samples.tpch.lineitem.l_shipmode`. The full value list was not confirmed by a source; session 10b's EDA should list the distinct values.
