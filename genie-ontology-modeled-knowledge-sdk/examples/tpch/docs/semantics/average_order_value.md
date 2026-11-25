---
term: Average Order Value
synonyms: [AOV, revenue per order]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Revenue, Order Volume]
sources:
  - https://scor.ascm.org/performance/assets/AM.3.17
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
Revenue divided by number of orders. This is a common commerce KPI, not one of the ASCM SCOR metrics ([SCOR Model](https://scor.ascm.org/performance/assets/AM.3.17)). Revenue is the TPC-H discounted price ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Business context
Shows whether sales grow through bigger orders or through more orders. Compare it across market segments, nations and order priorities.

## Data usage
Line-item basis: `sum(l_extendedprice * (1 - l_discount)) / count(distinct l_orderkey)` over `samples.tpch.lineitem`. Header basis: `avg(o_totalprice)` over `samples.tpch.orders`. The two differ by discount and tax, so the owner must pick one (see `docs/research/02_kpi_definitions.md`, Open questions).
