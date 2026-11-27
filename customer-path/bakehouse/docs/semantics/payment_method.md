---
term: Payment Method
synonyms: [tender type, payment type, tender]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Payment Method Mix, Cardholder Data, Sales Transaction]
sources: ['https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf']
---
## Definition

How a transaction is settled (cash, card, other); a tender line item records the settlement of a retail transaction with a valid tender type ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)).

## Business context

Payment method drives processing cost and cash-handling workload and indicates customer payment preferences.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Dimension `paymentMethod`.

## Values from EDA

values_from_eda: true

Columns: sales_transactions.paymentMethod (observed codes are listed by the deep EDA stage; meanings are not guessed here).
