---
term: Average Unit Price
synonyms: [average selling price, ASP]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Units Sold, Gross Sales Revenue]
sources: ['https://docs.oracle.com/cd/E79623_01/rms/pdf/192000/html/user_guide/glossary.htm']
---
## Definition

Average retail price per unit sold. Oracle Retail defines unit retail as the price in the selling unit of measure for an item and location ([Oracle Retail](https://docs.oracle.com/cd/E79623_01/rms/pdf/192000/html/user_guide/glossary.htm)).

## Business context

Tracks realised price by product and franchise.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) / sum(quantity). Row-level unitPrice is the list unit price.
