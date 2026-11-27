---
term: Customer Coverage
synonyms: [active customer rate, customer reach]
domain: bakehouse_retail_sales
subdomain: customers
related_terms: [Bakehouse Customer, Repeat Customer Rate]
sources: ['https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields']
---
## Definition

The share of known customers who bought at least once in a period, a purchase-frequency view of the customer base ([Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields)).

## Business context

Coverage shows how much of the registered customer base is active.

## Data usage

Source tables: samples.bakehouse.sales_customers, samples.bakehouse.sales_transactions

Proxy: share of customers in the customer table with at least one transaction, not a CRM activity definition.

count(DISTINCT sales_transactions.customerID) / count(DISTINCT sales_customers.customerID).
