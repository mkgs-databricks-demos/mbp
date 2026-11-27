---
term: Product
synonyms: [item, SKU, baked good, menu item]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Sales Transaction, Product Mix, Unit Price]
sources: ['https://www.nist.gov/document/00-20-h130-v-final-5pdf', 'https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf']
---
## Definition

The sellable item identified on a sale; a Stock-Keeping Unit (SKU) is a system of product identity and pricing ([NIST Handbook 130](https://www.nist.gov/document/00-20-h130-v-final-5pdf)).

## Business context

Product is the main dimension for menu and assortment decisions: which baked goods drive revenue and units at each franchise.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Dimension `product` (product name string; no separate product master table exists).

## Values from EDA

values_from_eda: true

Columns: sales_transactions.product (distinct product names are listed by the deep EDA stage).
