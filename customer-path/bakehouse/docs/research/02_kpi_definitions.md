# 02 KPI Definitions — bakehouse_retail_sales

## Summary
The standard retail and franchise sales KPIs are revenue, transaction count, units, average transaction value, basket size, revenue per customer, purchase frequency, repeat purchase and retention rates, payment mix, sales per store and comparable-store sales growth. Each has a published formula, cited below. The source tables have no discount, cost, refund or supplier-spend columns, so net sales, margin and spend-based supplier concentration cannot be computed. Where a defensible approximation exists it is marked as a proxy. All formulas are written against `samples.bakehouse.*` columns. Their grain assumes one row per transaction, which session 04 (EDA) must confirm.

## Findings

### KPI table
| kpi | formula | numerator | denominator | grain | time_period | source | candidate_tables | proxy |
|---|---|---|---|---|---|---|---|---|
| Gross Sales Revenue | sum(totalPrice) | sum(totalPrice) | — | transaction | any (day/week/month) | [Shopify: Average Transaction Value](https://www.shopify.com/blog/average-transaction-value) (total revenue input) | sales_transactions | no |
| Net Sales | gross sales − discounts − returns | — | — | transaction | any | [Shopify Analytics fields reference](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) | — | not computable |
| Transaction Count | count(distinct transactionID) | count(distinct transactionID) | — | transaction | any | [Shopify: Average Transaction Value](https://www.shopify.com/blog/average-transaction-value) | sales_transactions | no |
| Units Sold | sum(quantity) | sum(quantity) | — | transaction | any | [Shopify: Basket Size](https://www.shopify.com/blog/basket-size) | sales_transactions | no |
| Average Transaction Value | sum(totalPrice) / count(distinct transactionID) | total revenue | number of transactions | transaction | same period for both | [Shopify: Average Transaction Value](https://www.shopify.com/blog/average-transaction-value); [Shopify: AOV](https://www.shopify.com/blog/average-order-value) | sales_transactions | no |
| Units per Transaction (Basket Size) | sum(quantity) / count(distinct transactionID) | total units sold | number of transactions | transaction | same period | [Shopify: Basket Size](https://www.shopify.com/blog/basket-size); [Lightspeed: Retail KPIs](https://www.lightspeedhq.com/blog/retail-kpi/) | sales_transactions | no |
| Average Unit Price | sum(totalPrice) / sum(quantity) | total revenue | units sold | product x period | same period | [Oracle Retail Merchandising glossary](https://docs.oracle.com/cd/E79623_01/rms/pdf/192000/html/user_guide/glossary.htm) (unit retail definition; ratio derived) | sales_transactions | no |
| Revenue per Customer | sum(totalPrice) / count(distinct customerID) | total revenue | unique customers | customer x period | same period | [Shopify: Basket Size](https://www.shopify.com/blog/basket-size) ("average ticket size") | sales_transactions, sales_customers | no |
| Purchase Frequency | count(distinct transactionID) / count(distinct customerID) | number of purchases | unique customers | customer x period | same period | [Salesforce: Customer Retention](https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/) | sales_transactions | no |
| Repeat Purchase Rate | customers with >1 transaction / customers with >=1 transaction | repeat customers | purchasing customers | customer x period | window | [Salesforce: Customer Loyalty](https://www.salesforce.com/marketing/loyalty/customer-loyalty/) | sales_transactions | no |
| Customer Retention Rate | ((E − N) / S) x 100 | customers at end of period minus new customers | customers at start of period | customer x period | consecutive periods | [Salesforce: Customer Retention Rate](https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/) | sales_transactions | yes: buying customers in both the prior and the current period / buying customers in the prior period; no customer start date, so "active" means "made a purchase" |
| Customer Lifetime Value | average purchase value x purchase frequency x customer lifespan | — | — | customer | lifetime | [HubSpot: Customer Lifetime Value](https://blog.hubspot.com/service/how-to-calculate-customer-lifetime-value) | sales_transactions | yes: observed customer value = revenue per customer over the observed window; no lifespan data |
| Active Customer Rate | customers with >=1 transaction in window / customers in the customer table | active customers | all registered customers | customer x period | window | [Salesforce: Customer Retention Rate](https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/) (activity-window framing) | sales_transactions, sales_customers | no |
| Payment Mix Share | sum(totalPrice) for a paymentMethod / sum(totalPrice) | sales by payment method | total sales | payment method x period | same period | [Lightspeed K-Series: Sales Report dashboard](https://k-series-support.lightspeedhq.com/hc/en-us/articles/35539237853467-Understanding-the-Sales-Report-dashboard) | sales_transactions | no |
| Sales per Franchise | sum(totalPrice) / count(distinct franchiseID) | total sales | number of stores | franchise x period | same period | [Lightspeed: Navigating Lightspeed Analytics](https://retail-support.lightspeedhq.com/hc/en-us/articles/4410640218523-Navigating-Lightspeed-Analytics) | sales_transactions, sales_franchises | no |
| Average Unit Volume | annual sales per store | annual sales | number of stores | franchise x year | fiscal year | [QSR 50 (2025)](https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf) (average sales per unit) | sales_transactions, sales_franchises | yes: annualised from the observed window if it is shorter than one year |
| Same-Store Sales Growth | (current sales of comparable stores − prior sales of the same stores) / prior sales | change in comparable-store sales | prior-period comparable-store sales | franchise x period | year over year or period over period | [Wikipedia: Same-store sales](https://en.wikipedia.org/wiki/Same-store_sales) | sales_transactions, sales_franchises | no (requires at least two comparable periods; EDA confirms the date range) |
| Approved Supplier Rate | franchises whose supplier is approved / all franchises | franchises with an approved supplier | franchises | franchise | snapshot | [FoodDocs: Approved Suppliers List](https://www.fooddocs.com/food-safety-templates/approved-supplier-list) | sales_franchises, sales_suppliers | no (meaning of `approved` codes deferred to EDA) |
| Supplier Concentration | spend with top supplier(s) / total supplier spend x 100 | spend with top N suppliers | total spend | supplier | snapshot | [Franchising.com: Supplier Contracts and System Health](https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html) (dependency risk; formula is an industry convention) | sales_franchises, sales_suppliers, sales_transactions | yes: share of franchises (or of franchise sales) served by the top N suppliers, not spend; no purchase data |
| Gross Margin | (revenue − cost of goods sold) / revenue | — | — | — | — | [Shopify Analytics fields reference](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) | — | not computable |

### Notes
* Use the same period for the numerator and the denominator of every ratio ([Shopify: AOV](https://www.shopify.com/blog/average-order-value)).
* Basket size (units) and average ticket (value) are different measures ([Shopify: Basket Size](https://www.shopify.com/blog/basket-size)).
* Ratios must be computed as ratio-of-sums at the query grain, not as averages of row-level ratios. This is required so that metric view measures roll up correctly ([Kimball: Facts for Measurements](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/facts-for-measurement/)).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Revenue, ATV, revenue per customer | `sales_transactions.totalPrice`, `transactionID`, `customerID` | Measures |
| Units, basket size, average unit price | `sales_transactions.quantity`, `totalPrice` | Measures |
| Payment mix | `sales_transactions.paymentMethod` | Dimension + share measure |
| Sales per franchise, AUV, same-store growth | `sales_transactions.franchiseID`, `dateTime`; `sales_franchises` | Measures by franchise and period |
| Customer KPIs | `sales_transactions.customerID`, `dateTime`; `sales_customers` | Measures (window-based) |
| Supplier KPIs | `sales_franchises.supplierID`; `sales_suppliers.approved` | Measures; filter |

## Open questions
* Is `transactionID` unique per row? If a transaction can span rows, ATV and basket size must count distinct `transactionID`. The formulas above already do this.
* Does `totalPrice` = `quantity * unitPrice`? Prices are stored as integers; confirm the currency and units.
* What date range does `dateTime` cover? This decides whether same-store growth and retention can be computed.
* What do the `approved` and `paymentMethod` codes mean? Deferred to EDA.

## Sources
1. [What Is Average Transaction Value?](https://www.shopify.com/blog/average-transaction-value) — Shopify
2. [Average Order Value (AOV): Formula & Tips](https://www.shopify.com/blog/average-order-value) — Shopify, 2026
3. [Basket Size: How to Calculate and Increase It](https://www.shopify.com/blog/basket-size) — Shopify, 2026
4. [Shopify Analytics data points (fields) reference](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) — Shopify Help Center
5. [15 Retail KPIs Every Business Owner Should Know](https://www.lightspeedhq.com/blog/retail-kpi/) — Lightspeed
6. [Understanding the Sales Report dashboard](https://k-series-support.lightspeedhq.com/hc/en-us/articles/35539237853467-Understanding-the-Sales-Report-dashboard) — Lightspeed Restaurant
7. [Navigating Lightspeed Analytics](https://retail-support.lightspeedhq.com/hc/en-us/articles/4410640218523-Navigating-Lightspeed-Analytics) — Lightspeed Retail
8. [Same-store sales](https://en.wikipedia.org/wiki/Same-store_sales) — Wikipedia
9. [Customer retention rate: formula & improvement tips](https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/) — Salesforce
10. [Customer Retention: Definition, Strategies & Examples](https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/) — Salesforce EU
11. [What is Customer Loyalty?](https://www.salesforce.com/marketing/loyalty/customer-loyalty/) — Salesforce
12. [How to calculate customer lifetime value (CLV)](https://blog.hubspot.com/service/how-to-calculate-customer-lifetime-value) — HubSpot
13. [QSR 50, August 2025](https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf) — QSR Magazine, 2025
14. [Approved Suppliers List](https://www.fooddocs.com/food-safety-templates/approved-supplier-list) — FoodDocs
15. [Seizing an Opportunity: Supplier Contracts and System Health](https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html) — Franchising.com
16. [Oracle Retail Merchandising glossary](https://docs.oracle.com/cd/E79623_01/rms/pdf/192000/html/user_guide/glossary.htm) — Oracle
17. [Facts for Measurements](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/facts-for-measurement/) — Kimball Group
