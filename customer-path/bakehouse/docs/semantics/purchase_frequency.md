---
term: Purchase Frequency
synonyms: [visit frequency, purchases per customer]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Repeat Purchase Rate, Revenue per Customer]
sources: ['https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/']
---
## Definition

Total number of purchases divided by the number of unique customers in a period ([Salesforce](https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/)).

## Business context

Loyalty indicator. It feeds customer lifetime value.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count(distinct transactionID) / count(distinct customerID).
