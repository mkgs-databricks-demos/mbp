---
term: Unit Price
synonyms: [price, item price, price per unit]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units Sold, Gross Sales, Product]
sources: ['https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html']
---
## Definition

The price charged per unit of a product; unit pricing expresses cost per unit of measure ([NIST SP 1181 Unit Pricing Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html)).

## Business context

Unit price supports price-mix analysis and checks that line totals equal quantity times price.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Column `unitPrice` (integer; currency is not recorded in the data). Average selling price = sum(totalPrice) / sum(quantity).
