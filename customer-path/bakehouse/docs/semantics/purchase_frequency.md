---
term: Purchase Frequency
synonyms: [orders per customer, visit frequency, transactions per customer]
domain: bakehouse_retail_sales
subdomain: customers
related_terms: [Bakehouse Customer, Repeat Customer Rate, Revenue per Customer]
sources: ['https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields']
---
## Definition

The number of orders divided by the number of unique customers, as used in RFM customer grouping ([Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields)).

## Business context

Frequency shows how often customers return to a franchise; bakeries depend on habitual visits.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count(DISTINCT transactionID) / count(DISTINCT customerID) over the period.
