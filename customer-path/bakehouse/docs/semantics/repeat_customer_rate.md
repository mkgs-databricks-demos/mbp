---
term: Repeat Customer Rate
synonyms: [returning customer rate, repeat purchase rate]
domain: bakehouse_retail_sales
subdomain: customers
related_terms: [Purchase Frequency, Customer]
sources: ['https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields']
---
## Definition

The share of customers with more than one purchase in a period; RFM grouping uses purchase frequency ([Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields)).

## Business context

A high repeat rate indicates loyalty; a falling one is an early warning for a franchise.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count of customerIDs with count(DISTINCT transactionID) > 1 / count(DISTINCT customerID), per period.
