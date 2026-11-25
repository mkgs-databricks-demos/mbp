---
term: Extended Price
synonyms: [l_extendedprice, gross price, list price times quantity]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Revenue, Gross Charge, Discount Revenue, Line Item, Part]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
The undiscounted price of a line item, generated as `l_quantity * p_retailprice` ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
The base amount for every revenue formula in TPC-H. Revenue, discount revenue and gross charge all apply discount or tax to it ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Data usage
`samples.tpch.lineitem.l_extendedprice`. Sum it for gross sales before discount: `sum(l_extendedprice)`. It already includes quantity, so never multiply it by `l_quantity`.
