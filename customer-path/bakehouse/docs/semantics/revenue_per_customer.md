---
term: Revenue per Customer
synonyms: [average revenue per customer, average ticket size per customer]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Gross Sales Revenue, Purchase Frequency]
sources: ['https://www.shopify.com/blog/basket-size']
---
## Definition

Total sales revenue divided by the number of unique customers ([Shopify](https://www.shopify.com/blog/basket-size)).

## Business context

Customer value measure used for segmentation.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) / count(distinct customerID).
