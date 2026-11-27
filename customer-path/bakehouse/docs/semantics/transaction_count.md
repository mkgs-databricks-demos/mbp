---
term: Transaction Count
synonyms: [number of transactions, ticket count, order count]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Gross Sales Revenue, Average Transaction Value]
sources: ['https://www.shopify.com/blog/average-transaction-value']
---
## Definition

Number of POS transactions in a period ([Shopify](https://www.shopify.com/blog/average-transaction-value)).

## Business context

Measures store traffic. It is the denominator of average transaction value and basket size.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count(distinct transactionID).
