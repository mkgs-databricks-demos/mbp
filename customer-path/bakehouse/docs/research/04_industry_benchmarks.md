# 04 Industry Benchmarks — bakehouse_retail_sales

## Summary
Public benchmarks for bakery cafes and quick-service franchises cover mainly average unit volume (AUV) and, in some FDD excerpts, average ticket. The Federal Reserve Diary of Consumer Payment Choice gives a US-wide payment mix across all consumer payments, not restaurants only. No public source was found for items per transaction, repeat purchase rate, same-store growth, approved-supplier rate or supplier concentration for this segment; those rows say `not found`. The source data is synthetic, so any benchmark is directional only.

## Findings

### Benchmark table
| kpi | value_or_range | tier | as_of | source |
|---|---|---|---|---|
| Average Transaction Value (bakery cafe) | $27.03 average; $26.93 median | brand system average / median (one bakery-cafe brand) | 2024 FDD excerpt | [FranChimp: 2024 FDD excerpt](https://www.franchimp.com/pdfjs/read.php?f=101587_2024.pdf) |
| Average Unit Volume (bakery cafe, franchisee-owned) | $2,599,432 | brand average | fiscal year ending 2018-12-25, as stated in the FDD reproduction | [FranChimp: Panera Bread FDD](https://www.franchimp.com/?f=107274_2026.pdf&page=pdf) |
| Average Unit Volume (bakery cafe, company + franchisee) | $2,739,908 | brand average | fiscal year ending 2018-12-25 | [FranChimp: Panera Bread FDD](https://www.franchimp.com/?f=107274_2026.pdf&page=pdf) |
| Average Unit Volume (bakery franchise concept) | $696,600 | single-brand franchise AUV | 2024 | [QSR Magazine: The 16 Best Restaurant Franchising Deals for 2024](https://www.qsrmagazine.com/story/the-16-best-restaurant-franchising-deals-for-2024/) |
| Average Unit Volume (limited-service example) | $1,005 thousand average sales per unit | single brand in QSR 50 | 2024 data (2025 edition) | [QSR 50, August 2025](https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf) |
| Payment Mix Share — cash | 16% of all US consumer payments | national, all merchants | 2023 data (2024 report) | [Federal Reserve: 2024 Findings from the Diary of Consumer Payment Choice](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf) |
| Payment Mix Share — credit card | 32% of all US consumer payments | national, all merchants | 2023 data | [Federal Reserve Diary 2024](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf) |
| Payment Mix Share — debit card | 30% of all US consumer payments | national, all merchants | 2023 data | [Federal Reserve Diary 2024](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf) |
| Payment Mix Share — mobile app | not found (not separately labelled in the report) | — | — | [Federal Reserve Diary 2024](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf) |
| Units per Transaction (Basket Size) | not found | — | — | — |
| Repeat Purchase Rate | not found | — | — | — |
| Customer Retention Rate | not found | — | — | — |
| Same-Store Sales Growth | not found | — | — | — |
| Approved Supplier Rate | not found | — | — | — |
| Supplier Concentration | not found | — | — | — |

### Caveats
* The average-ticket and AUV figures come from franchise disclosure documents, which are Item 19 representations under the [FTC Franchise Rule](https://www.ftc.gov/legal-library/browse/rules/franchise-rule). They describe one brand, not the segment.
* The Federal Reserve payment mix covers all consumer payments, not restaurant POS only ([Federal Reserve Diary 2024](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf)).
* The bakehouse dataset is synthetic ([dataset listing](https://www.selectdataset.com/dataset/8ce7ecbe16c0a62866e1786c900b085e)). Use benchmarks to sanity-check orders of magnitude, not as targets.

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Average ticket benchmark | `sales_transactions.totalPrice`, `transactionID` | Comparison for the Average Transaction Value measure (glossary page context) |
| AUV benchmarks | `sales_transactions.totalPrice`, `franchiseID`, `dateTime` | Comparison for Sales per Franchise / AUV |
| Payment mix | `sales_transactions.paymentMethod` | Comparison for Payment Mix Share |

## Open questions
* What currency and price units do `unitPrice` and `totalPrice` use? Integer prices may not compare directly with USD benchmarks.
* Does the observed window cover a full year? AUV comparison needs annualisation otherwise.

## Sources
1. [Franchise Disclosure Document (2024 excerpt)](https://www.franchimp.com/pdfjs/read.php?f=101587_2024.pdf) — FranChimp reproduction, 2024
2. [2026 Franchise Disclosure Document for Panera Bread Bakery-Cafe](https://www.franchimp.com/?f=107274_2026.pdf&page=pdf) — FranChimp reproduction
3. [The 16 Best Restaurant Franchising Deals for 2024](https://www.qsrmagazine.com/story/the-16-best-restaurant-franchising-deals-for-2024/) — QSR Magazine, 2024
4. [QSR 50, August 2025](https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf) — QSR Magazine, 2025
5. [2024 Findings from the Diary of Consumer Payment Choice](https://www.frbservices.org/wp-content/uploads/2024-diary-of-consumer-payment-choice.pdf) — Federal Reserve Financial Services, 2024
6. [Franchise Rule](https://www.ftc.gov/legal-library/browse/rules/franchise-rule) — US Federal Trade Commission
7. [Cookies Dataset DAIS 2024 (Bakehouse dataset listing mirror)](https://www.selectdataset.com/dataset/8ce7ecbe16c0a62866e1786c900b085e) — SelectDataset
