# 02 KPI Definitions — bakehouse_retail_sales

## Summary
The standard retail and franchise KPIs for this domain are ratios of gross sales, units and transaction or customer counts. Formulas come from retail analytics vendors and retailer SEC filings. The source tables support most KPIs directly; net sales is not computable (no returns or discounts), and comparable sales, supplier coverage and customer coverage are proxies. Measure names below are what metric view synthesis (session 05) should use.

## Findings

### KPI table
| kpi | formula | numerator | denominator | grain | time_period | source | candidate_tables | proxy |
|---|---|---|---|---|---|---|---|---|
| Gross Sales | sum(totalPrice) | sum(totalPrice) | — | any (product, franchise, city, country, customer) | any | [IFA glossary](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/) | sales_transactions | no |
| Net Sales | gross sales - returns - allowances - discounts | net sales | — | any | any | [SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm) | — | not computable |
| Units Sold | sum(quantity) | sum(quantity) | — | any | any | [Shopify: Basket Size](https://www.shopify.com/blog/basket-size) | sales_transactions | no |
| Transaction Count | count(DISTINCT transactionID) | transactions | — | any | any | [Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf) | sales_transactions | no |
| Average Transaction Value | sum(totalPrice) / count(DISTINCT transactionID) | gross sales | transactions | franchise, product, period | any | [Shopify: Average Order Value](https://www.shopify.com/blog/average-order-value) | sales_transactions | no |
| Units per Transaction | sum(quantity) / count(DISTINCT transactionID) | units | transactions | franchise, period | any | [Shopify: Basket Size](https://www.shopify.com/blog/basket-size) | sales_transactions | no |
| Average Selling Price | sum(totalPrice) / sum(quantity) | gross sales | units | product | any | [NIST SP 1181 Unit Pricing Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html) | sales_transactions | no |
| Product Mix | sum(totalPrice) by product / sum(totalPrice) | product sales | total sales in scope | product within franchise, city, country | any | [NielsenIQ: Rate of Sale Metrics](https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf) | sales_transactions | no |
| Payment Method Mix | count(DISTINCT transactionID) by paymentMethod / count(DISTINCT transactionID) | transactions by method | all transactions | payment method within franchise, country | any | [Lightspeed: built-in reports](https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom) | sales_transactions | no |
| Sales per Franchise | sum(totalPrice) / count(DISTINCT franchiseID) | gross sales | franchises with sales | city, country, size | any (annualized = AUV) | [NielsenIQ: Rate of Sale Metrics](https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf) | sales_transactions, sales_franchises | no |
| Comparable Franchise Sales Growth | (sales current - sales prior) / sales prior, franchises in both periods | change in sales | prior-period sales | franchise set | period over prior period | [SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm); [TJX SEC filing](https://investor.tjx.com/node/19916/html) | sales_transactions, sales_franchises | yes: franchises with sales in both periods, not stores open 12 months; gross, not net, sales |
| Revenue per Customer | sum(totalPrice) / count(DISTINCT customerID) | gross sales | customers who bought | customer geography | any | [Lightspeed: built-in reports](https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom) | sales_transactions, sales_customers | no |
| Purchase Frequency | count(DISTINCT transactionID) / count(DISTINCT customerID) | transactions | customers who bought | customer geography | any | [Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) | sales_transactions | no |
| Repeat Customer Rate | customers with > 1 transaction / customers who bought | repeat customers | customers who bought | customer geography | per period | [Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) | sales_transactions | no |
| Customer Coverage | count(DISTINCT sales_transactions.customerID) / count(DISTINCT sales_customers.customerID) | customers who bought | known customers | customer geography | per period | [Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) | sales_customers, sales_transactions | yes: share of customer-table customers with at least one transaction, not a CRM activity definition |
| Supplier Coverage | count(DISTINCT franchiseID) by supplierID | franchises served | — (or suppliers with franchises / all suppliers) | supplier, ingredient, approved | snapshot | [IFA glossary](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/) | sales_franchises, sales_suppliers | yes: count of franchises mapped to a supplier, not purchase volume |
| Approved Supplier Share | approved suppliers / all suppliers (or franchises on approved suppliers / all franchises) | approved suppliers | suppliers | supplier geography | snapshot | [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide) | sales_suppliers, sales_franchises | no (approved code meaning from EDA) |

### Notes
* Comparable sales definitions vary: stores open at least twelve months ([SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm)) or from the third fiscal year of operation ([TJX SEC filing](https://investor.tjx.com/node/19916/html)). The data has no store opening date, hence the proxy; it also needs a data span longer than one comparison period (EDA checks `dateTime` range).
* Name proxy measures so they are not mistaken for the standard (e.g. `Comparable Franchise Sales Growth (proxy)`).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Revenue = gross sales | sales_transactions.totalPrice | measure Gross Sales; base of ATV, mix, per-franchise and per-customer KPIs |
| Basket KPIs | sales_transactions.quantity, transactionID | measures Units Sold, Units per Transaction |
| Payment mix | sales_transactions.paymentMethod | dimension + ratio measure |
| Store productivity | sales_transactions.franchiseID, sales_franchises | measure Sales per Franchise; geography dimensions |
| Customer KPIs | sales_transactions.customerID, sales_customers | measures Revenue per Customer, Purchase Frequency, Repeat Customer Rate, Customer Coverage |
| Supply KPIs | sales_franchises.supplierID, sales_suppliers.approved | measures Supplier Coverage, Approved Supplier Share |

## Open questions
* Is totalPrice always quantity * unitPrice? (EDA)
* Row grain of sales_transactions; if one row per transaction, Units per Transaction = avg(quantity). (EDA)
* Date span of dateTime, to decide whether comparable sales is meaningful. (EDA)

## Sources
1. [Shopify: Average Order Value](https://www.shopify.com/blog/average-order-value) — Shopify
2. [Shopify: Average Transaction Value](https://www.shopify.com/blog/average-transaction-value) — Shopify
3. [Shopify: Basket Size](https://www.shopify.com/blog/basket-size) — Shopify
4. [Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) — Shopify
5. [Lightspeed: built-in reports](https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom) — Lightspeed
6. [NielsenIQ: Rate of Sale Metrics](https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf) — NielsenIQ, 2021
7. [SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm) — U.S. SEC EDGAR, 2006
8. [TJX SEC filing](https://investor.tjx.com/node/19916/html) — The TJX Companies
9. [IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/) — International Franchise Association
10. [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide) — Federal Trade Commission
11. [Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf) — Oracle
12. [NIST SP 1181 Unit Pricing Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html) — NIST, 2025 edition
