---
term: Gross Sales Revenue
synonyms: [revenue, sales, total sales]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Transaction Count, Average Transaction Value]
sources: ['https://www.shopify.com/blog/average-transaction-value']
---
## Definition

Total value of goods sold in a period, before discounts, returns and taxes ([Shopify](https://www.shopify.com/blog/average-transaction-value)).

## Business context

The headline sales measure for the franchise system, tracked by product, franchise, geography and time.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) over transactions in the period. Net sales and margin are not computable: there are no discount, return or cost columns.
