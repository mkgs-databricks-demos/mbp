---
term: Average Transaction Value
synonyms: [ATV, average ticket, average check, average order value, AOV]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Gross Sales Revenue, Transaction Count]
sources: ['https://www.shopify.com/blog/average-transaction-value', 'https://www.shopify.com/blog/average-order-value']
---
## Definition

Total revenue divided by the number of transactions in the same period ([Shopify](https://www.shopify.com/blog/average-transaction-value)).

## Business context

Shows how much each visit is worth. Upsell and pricing decisions target it.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) / count(distinct transactionID) at the query grain (ratio of sums).
