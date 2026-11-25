---
term: Gross Charge
synonyms: [sum_charge, charged amount, revenue including tax]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Revenue, Extended Price]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The amount charged to the customer after discount and tax, `l_extendedprice * (1 - l_discount) * (1 + l_tax)`. TPC-H Q1 reports it as `sum_charge` ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Part of the Q1 pricing summary report, which groups shipped line items by return flag and line status ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). Finance uses it to reconcile billed amounts with revenue.

## Data usage
`sum(l_extendedprice * (1 - l_discount) * (1 + l_tax))` over `samples.tpch.lineitem`. Grain: line item. Q1 filters on a ship-date cutoff and groups by `l_returnflag`, `l_linestatus`.
