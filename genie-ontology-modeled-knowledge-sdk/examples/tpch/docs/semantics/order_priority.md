---
term: Order Priority
synonyms: [o_orderpriority, priority]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Late Receipt, Ship Mode, Order Volume]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The urgency a customer assigns to an order. There are five values: 1-URGENT, 2-HIGH, 3-MEDIUM, 4-NOT SPECIFIED and 5-LOW ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
TPC-H Q12 splits late line items into high priority (1-URGENT or 2-HIGH) and low priority (everything else) by ship mode ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). This checks whether cheaper ship modes hurt urgent orders.

## Data usage
Dimension `samples.tpch.orders.o_orderpriority`. High-priority flag: `o_orderpriority in ('1-URGENT', '2-HIGH')`.
