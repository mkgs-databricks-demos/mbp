---
term: Units Sold
synonyms: [quantity, units, items sold]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units per Transaction, Product, Gross Sales]
sources: ['https://www.shopify.com/blog/basket-size', 'https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf']
---
## Definition

The number of product units sold on sale line items ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf); [Shopify: Basket Size](https://www.shopify.com/blog/basket-size)).

## Business context

Units show volume independent of price, so they separate demand changes from price changes.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(quantity) over transaction rows.
