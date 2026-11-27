---
term: Repeat Purchase Rate
synonyms: [repeat customer rate]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Purchase Frequency, Customer Retention Rate]
sources: ['https://www.salesforce.com/marketing/loyalty/customer-loyalty/']
---
## Definition

Percentage of customers who make more than one purchase ([Salesforce](https://www.salesforce.com/marketing/loyalty/customer-loyalty/)).

## Business context

Measures loyalty and the effect of retention programmes.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count(customers with >1 distinct transactionID) / count(customers with >=1) in the window.
