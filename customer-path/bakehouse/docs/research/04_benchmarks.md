# 04 Industry Benchmarks — bakehouse_retail_sales

## Summary
Public benchmarks for bakery franchises are sparse. Payment mix has strong primary data (Federal Reserve Diary of Consumer Payment Choice). Spend benchmarks exist for cafes and bakeries at item level (Toast), and average unit volume is published per brand in franchise disclosure documents (third-party summaries). No authoritative public benchmark was found for bakery items per transaction or repeat customer rate. The source data is a sample dataset, so benchmarks are context only, not targets.

## Findings

| kpi | value_or_range | tier | as_of | source |
|---|---|---|---|---|
| Payment Method Mix (cash share of all US consumer payments) | 16% | US all payments | 2023 payments | [Federal Reserve: 2024 Diary of Consumer Payment Choice](https://www.frbservices.org/news/research/2024-diary-of-consumer-payment-choice/) |
| Payment Method Mix (credit card share) | 32% | US all payments | 2023 | [Atlanta Fed: 2023 Survey and Diary of Consumer Payment Choice](https://www.atlantafed.org/research-and-data/surveys/survey-and-diary-of-consumer-payment-choice/2023-survey-and-diary) |
| Payment Method Mix (debit card share) | 30% | US all payments | 2023 | [Atlanta Fed: 2023 Survey and Diary of Consumer Payment Choice](https://www.atlantafed.org/research-and-data/surveys/survey-and-diary-of-consumer-payment-choice/2023-survey-and-diary) |
| Payment Method Mix (restaurants, payments per consumer per month) | cash 4, credit 6, debit 6 | US restaurants | 2024 | [Federal Reserve: 2025 Findings from the Diary of Consumer Payment Choice](https://www.frbservices.org/wp-content/uploads/2025-diary-of-consumer-payment-choice.pdf) |
| Average spend per food item (cafes and bakeries) | about $8 | Toast cafe & bakery cohort | Q2 2023 | [Toast: Cafe & Bakery Insights](https://pos.toasttab.com/es-us/news/most-popular-alcohol-by-state-toast-restaurant-trends-report) |
| Average spend per beverage (cafes and bakeries) | about $6 | Toast cafe & bakery cohort | Q2 2023 | [Toast: Cafe & Bakery Insights](https://pos.toasttab.com/es-us/news/most-popular-alcohol-by-state-toast-restaurant-trends-report) |
| Sales per Franchise (AUV, coffee/smoothie cafe brand) | $1,005,063 | one brand (Tropical Smoothie Cafe, FDD Item 19) | FY2024 | [Rootsmodel: Coffee shop & bakery benchmarks](https://rootsmodel.com/benchmarks/coffee-shops) |
| Average Transaction Value (bakery franchise) | not found | — | — | — |
| Units per Transaction (bakery franchise) | not found | — | — | — |
| Repeat Customer Rate (bakery) | not found | — | — | — |
| Comparable Franchise Sales Growth (bakery) | not found | — | — | — |
| Supplier Coverage | not found | — | — | — |

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| US payment mix | sales_transactions.paymentMethod | context in Payment Method Mix page and metric comment |
| Cafe/bakery item spend | sales_transactions.unitPrice, totalPrice | context for Average Selling Price (currency of the data is unknown, so no direct comparison) |
| AUV | sales_transactions.totalPrice, sales_franchises | context for Sales per Franchise |

## Open questions
* Currency and price scale of the sample data (integer prices) before any benchmark comparison.
* Whether the owner has internal targets to replace the `not found` rows.

## Sources
1. [Federal Reserve: 2024 Diary of Consumer Payment Choice](https://www.frbservices.org/news/research/2024-diary-of-consumer-payment-choice/) — Federal Reserve Financial Services, 2024
2. [Atlanta Fed: 2023 Survey and Diary of Consumer Payment Choice](https://www.atlantafed.org/research-and-data/surveys/survey-and-diary-of-consumer-payment-choice/2023-survey-and-diary) — Federal Reserve Bank of Atlanta, 2023
3. [Federal Reserve: 2025 Findings from the Diary of Consumer Payment Choice](https://www.frbservices.org/wp-content/uploads/2025-diary-of-consumer-payment-choice.pdf) — Federal Reserve Financial Services, 2025
4. [Toast: Cafe & Bakery Insights](https://pos.toasttab.com/es-us/news/most-popular-alcohol-by-state-toast-restaurant-trends-report) — Toast, 2023
5. [Rootsmodel: Coffee shop & bakery benchmarks](https://rootsmodel.com/benchmarks/coffee-shops) — Rootsmodel (FDD summaries)
