---
term: Units Sold
synonyms: [quantity sold, items sold]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units per Transaction, Average Unit Price]
sources: ['https://www.shopify.com/blog/basket-size']
---
## Definition

Total number of product units sold in a period ([Shopify](https://www.shopify.com/blog/basket-size)).

## Business context

Volume measure used for product mix and production planning.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(quantity).
