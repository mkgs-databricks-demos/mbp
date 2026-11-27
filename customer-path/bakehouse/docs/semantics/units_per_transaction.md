---
term: Units per Transaction
synonyms: [UPT, basket size, items per transaction, average basket size]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units Sold, Sales Transaction, Average Transaction Value]
sources: ['https://www.shopify.com/blog/basket-size']
---
## Definition

The average number of units in one transaction (basket) ([Shopify: Basket Size](https://www.shopify.com/blog/basket-size)).

## Business context

Basket size shows whether customers buy one item or several; it is a lever for cross-selling.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(quantity) / count(DISTINCT transactionID). Grain of a row (one product line per transactionID, or one row per transaction) is confirmed by the deep EDA stage (docs/data_profiles/).
