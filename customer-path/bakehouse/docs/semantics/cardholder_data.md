---
term: Cardholder Data
synonyms: [card number, PAN, primary account number, payment card data]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Payment Method, Bakehouse Customer]
sources: ['https://www.pcisecuritystandards.org/document_library/', 'https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code']
---
## Definition

Payment card account data protected by PCI DSS (current version v4.0.1), which applies wherever card data is stored, processed or transmitted ([PCI Security Standards Council: Document Library](https://www.pcisecuritystandards.org/document_library/)).

## Business context

Card numbers must never appear in metrics, dashboards or Genie answers; the Databricks bakehouse tutorial drops cardNumber in its cleaned layer ([Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code)).

## Data usage

Source tables: samples.bakehouse.sales_transactions

Column `cardNumber`: exclude from all metric views and agent instructions; never a dimension or measure.
