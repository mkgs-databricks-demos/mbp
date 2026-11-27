---
term: Average Transaction Value
synonyms: [ATV, average ticket, average order value, AOV, average check]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Gross Sales, Sales Transaction, Units per Transaction]
sources: ['https://www.shopify.com/blog/average-transaction-value', 'https://www.shopify.com/blog/average-order-value']
---
## Definition

Total revenue divided by the number of transactions (orders) ([Shopify: Average Order Value](https://www.shopify.com/blog/average-order-value); [Shopify: Average Transaction Value](https://www.shopify.com/blog/average-transaction-value)).

## Business context

Average ticket tracks how much each customer visit is worth; franchises raise it through upselling and bundles.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) / count(DISTINCT transactionID), per franchise, product or period.
