---
term: Payment Mix Share
synonyms: [tender mix, payment share]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Payment Method, Gross Sales Revenue]
sources: ['https://k-series-support.lightspeedhq.com/hc/en-us/articles/35539237853467-Understanding-the-Sales-Report-dashboard']
---
## Definition

Share of sales paid with each payment method: sales by method divided by total sales ([Lightspeed](https://k-series-support.lightspeedhq.com/hc/en-us/articles/35539237853467-Understanding-the-Sales-Report-dashboard)).

## Business context

Informs payment acceptance strategy and fee negotiations.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) for a paymentMethod / sum(totalPrice) over the same period.

## Values from EDA

values_from_eda: true

Column: sales_transactions.paymentMethod
