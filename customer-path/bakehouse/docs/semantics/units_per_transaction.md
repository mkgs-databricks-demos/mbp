---
term: Units per Transaction
synonyms: [basket size, UPT, items per transaction]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units Sold, Transaction Count]
sources: ['https://www.shopify.com/blog/basket-size', 'https://www.lightspeedhq.com/blog/retail-kpi/']
---
## Definition

Total units sold divided by the number of transactions ([Shopify](https://www.shopify.com/blog/basket-size)).

## Business context

Measures basket depth. It is distinct from average ticket, which measures value.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(quantity) / count(distinct transactionID).
