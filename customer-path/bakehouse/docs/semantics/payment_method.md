---
term: Payment Method
synonyms: [tender type, payment type]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Payment Mix Share]
sources: ['https://docs.oracle.com/cd/E69213_01/pdf/1800025/html/user_guide/dimensions_attributes.htm']
---
## Definition

The form of payment used for a sale, for example cash, credit card or gift card ([Oracle Retail Insights](https://docs.oracle.com/cd/E69213_01/pdf/1800025/html/user_guide/dimensions_attributes.htm)).

## Business context

Used to analyse payment mix and processing cost.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Dimension: paymentMethod. Never use cardNumber (PCI DSS; see docs/research/03).

## Values from EDA

values_from_eda: true

Column: sales_transactions.paymentMethod
