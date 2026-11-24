---
term: Perfect Order Rate
synonyms: [perfect order fulfillment, perfect order performance]
domain: tpch_supply_chain
subdomain: fulfillment
related_terms: [On-Time Shipping Rate, Return Rate]
sources:
  - https://scor.ascm.org/performance/reliability/RL.1.1
  - https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance
---

## Definition
The share of orders that meet every delivery expectation: on time, complete, accurately documented and undamaged. SCOR RL.1.1 computes it as total perfect orders divided by total orders, times 100% ([SCOR Model RL.1.1](https://scor.ascm.org/performance/reliability/RL.1.1)).

## Business context
An end-to-end reliability KPI. APQC reports a cross-industry median of 88.0%, with 82.0% at the 25th percentile and 93.0% at the 75th ([Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance)).

## Data usage
Not yet mapped: TPC-H has no damage, documentation or invoice-accuracy columns. A partial proxy: an order counts as perfect when every line was received by `l_commitdate` and none has `l_returnflag = 'R'`. Label it as a proxy if built.
