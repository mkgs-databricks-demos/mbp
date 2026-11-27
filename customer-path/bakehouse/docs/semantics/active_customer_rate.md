---
term: Active Customer Rate
synonyms: [customer coverage, active customers]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Customer, Repeat Purchase Rate]
sources: ['https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/']
---
## Definition

Share of registered customers who made at least one purchase in the period. Customer activity is measured over a defined window ([Salesforce](https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/)).

## Business context

Shows how much of the customer base is engaged.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_customers

count(distinct customerID in transactions in window) / count(customerID in sales_customers).
