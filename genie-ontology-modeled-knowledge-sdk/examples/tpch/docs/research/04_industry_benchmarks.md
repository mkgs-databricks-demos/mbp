# 04 Industry Benchmarks — tpch_supply_chain

## Summary
TPC-H data is synthetic, so these benchmarks describe real wholesale and supply-chain operations, not the dataset's expected values. APQC Open Standards Benchmarking publishes cross-industry medians for perfect order performance, order fill rate, orders shipped complete and on time, and product return rate ([Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance)). NAW / MDM publishes mid-market distributor ranges for on-time delivery and OTIF ([The KPIs Raising the Bar for Mid-Market Distributors | NAW](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/)). Revenue, discount, market share and profit have no meaningful external benchmark for synthetic data.

## Findings

### Benchmark table
| kpi | value_or_range | tier | as_of | source |
|---|---|---|---|---|
| Perfect order performance | 88.0% | median | not stated (page retrieved 2026-11-24) | [Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance) |
| Perfect order performance | 82.0% | 25th percentile | not stated (page retrieved 2026-11-24) | [Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance) |
| Perfect order performance | 93.0% | 75th percentile | not stated (page retrieved 2026-11-24) | [Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance) |
| Order fill rate | 94.0% | median | not stated | [Order fill rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/order-fill-rate) |
| Orders shipped complete and on time | 93.0% | median | not stated | [Percentage of orders shipped complete and on time | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/percentage-orders-shipped-complete-and) |
| Average annual product return rate | 7.0% | median | not stated | [Average annual product return rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/average-annual-product-return-rate) |
| On-time delivery (mid-market distributors) | 85-90% | average | 2026-08-07 | [The KPIs Raising the Bar for Mid-Market Distributors | NAW](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/) |
| On-time delivery (mid-market distributors) | 95-98% | best in class | 2026-08-07 | [The KPIs Raising the Bar for Mid-Market Distributors | NAW](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/) |
| OTIF (on time in full) | 80-85% (target >= 95%) | average | 2026-08-07 | [The KPIs Raising the Bar for Mid-Market Distributors | NAW](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/) |
| Supplier on-time delivery | not found (APQC tracks the measure; no value in the retrieved page) | — | — | [Percentage of supplier on-time delivery | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/percentage-supplier-time-delivery) |
| Revenue, discount revenue, average order value, market share, profit, inventory value | not found | — | — | — |

### Definitions behind the benchmarks
* APQC defines a perfect order as one taken correctly, with inventory allocated immediately, delivered on time and invoiced accurately ([Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance)).
* APQC marks order fill rate as a logistics KPI ([Order fill rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/order-fill-rate)).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| On-time delivery and shipped-on-time medians | `lineitem.l_shipdate`, `l_commitdate`, `l_receiptdate` | reference ranges on the On-Time Shipping Rate page; not thresholds for synthetic data |
| Return rate median | `lineitem.l_returnflag` | reference range on the Return Rate page |
| Perfect order | not mappable (no damage or invoice data) | page context only |

## Open questions
* The APQC pages do not show an `as_of` date in the retrieved snippets; confirm on the page before quoting.
* Whether to show external benchmarks next to synthetic values at all (they can mislead users of a demo dataset).

## Sources
1. [Perfect order performance | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/perfect-order-performance) — APQC
2. [Order fill rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/order-fill-rate) — APQC
3. [Percentage of orders shipped complete and on time | APQC](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/percentage-orders-shipped-complete-and) — APQC
4. [Average annual product return rate | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/average-annual-product-return-rate) — APQC
5. [Percentage of supplier on-time delivery | APQC](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/percentage-supplier-time-delivery) — APQC
6. [The KPIs Raising the Bar for Mid-Market Distributors](https://www.naw.org/mdm/posts/the-kpis-raising-the-bar-for-mid-market-distributors/) — National Association of Wholesaler-Distributors, 2026-08-07
