---
term: Return Rate
synonyms: [product return rate, returns percentage]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [Return Flag, Line Item, Perfect Order Rate]
sources:
  - https://scor.ascm.org/performance/assets/AM.3.8
  - https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/average-annual-product-return-rate
  - https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf
---

## Definition
The share of shipped product that is returned. SCOR defines it by weight: weight of products returned divided by weight of products shipped, times 100% ([SCOR Model AM.3.8](https://scor.ascm.org/performance/assets/AM.3.8)).

## Business context
APQC reports a median average annual product return rate of 7.0% ([Average annual product return rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/average-annual-product-return-rate)). TPC-H Q10 reports revenue lost on returned items by customer ([TPC-H Specification v2.18.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v2.18.0.pdf)).

## Data usage
TPC-H has no weight column. Proxy on `samples.tpch.lineitem`, where returned items have `l_returnflag = 'R'` (Q10): by quantity `sum(case when l_returnflag = 'R' then l_quantity else 0 end) / sum(l_quantity)`, or by line count. The owner picks the basis.
