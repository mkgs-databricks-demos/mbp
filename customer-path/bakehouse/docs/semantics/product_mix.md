---
term: Product Mix
synonyms: [sales mix, product share, menu mix]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Product, Gross Sales, Units Sold]
sources: ['https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf']
---
## Definition

Each product's share of total sales, used to compare products' contribution ([NielsenIQ: Rate of Sale Metrics](https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf)).

## Business context

Product mix shows which baked goods carry each franchise and how assortment differs by city or country.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) by product / sum(totalPrice) over the same scope; unit variant uses sum(quantity).
