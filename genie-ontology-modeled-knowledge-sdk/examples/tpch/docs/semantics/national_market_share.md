---
term: National Market Share
synonyms: [market share, mkt_share, nation share of volume]
domain: tpch_supply_chain
subdomain: sales
related_terms: [Revenue, Supplier, Part]
sources:
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The share of revenue volume in a region that a given nation supplies. TPC-H Q8 computes it as `sum(case when nation = '[NATION]' then volume else 0 end) / sum(volume)`, with `volume = l_extendedprice * (1 - l_discount)` ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). The result is a fraction between 0 and 1 (0.04 = 4%), not a percentage.

## Business context
Q8 tracks how one nation's share changed across 1995-1996 for a given region and part type ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)). It is used to compare supplier nations' positions in a market.

## Data usage
Join `lineitem` to `orders` (order year), `customer` -> `nation` -> `region` (customer region filter), `supplier` -> `nation` (supplier nation that is the numerator), and `part` (`p_type` filter). Ratio of `sum(volume)` for the supplier nation over total `sum(volume)`, by `year(o_orderdate)`. In the metric views: `MEASURE(Market Volume) FILTER (WHERE Supplier Nation = '<nation>') / MEASURE(Market Volume)` on `mv_tpch_supply_chain_market_share`, kept as a 0-1 fraction. "Across all years" means one ratio over every year (no year grouping).
