---
term: Product
synonyms: [SKU, item, baked good]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units Sold, Average Unit Price]
sources: ['https://cdn.nrf.com/sites/default/files/2018-10/Vend_Inventory_Management_Guide.pdf']
---
## Definition

An item sold, identified by a stock-keeping unit (SKU) ([NRF / Vend](https://cdn.nrf.com/sites/default/files/2018-10/Vend_Inventory_Management_Guide.pdf)).

## Business context

Product mix drives menu, production and promotion decisions.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Dimension: product.

## Values from EDA

values_from_eda: true

Column: sales_transactions.product
