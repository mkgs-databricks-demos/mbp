---
term: Part
synonyms: [product, item, SKU, p_partkey]
domain: tpch_supply_chain
subdomain: procurement
related_terms: [Supplier, Supply Cost, Inventory Value, Extended Price]
sources:
  - https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf
---

## Definition
A product the wholesaler sells. PART is one of the eight TPC-H tables and links to suppliers through PARTSUPP ([TPC-H Specification v3.0.1](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPC-H_v3.0.1.pdf)). Its retail price sets the line-item extended price (`l_quantity * p_retailprice`) ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Business context
The product dimension for revenue, profit and market share. TPC-H Q8 and Q9 filter by part type or name ([TPC-H Specification v2.17.3](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.17.3.pdf)).

## Data usage
`samples.tpch.part`, key `p_partkey`. Attributes: `p_type`, `p_brand`, `p_mfgr`, `p_size`, `p_container`, `p_retailprice`. Join `lineitem` on `l_partkey` and `partsupp` on `ps_partkey`.
