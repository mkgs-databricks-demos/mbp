---
term: Payment Method Mix
synonyms: [tender mix, payment mix, payment share]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Payment Method, Gross Sales, Sales Transaction]
sources: ['https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom', 'https://www.frbservices.org/news/research/2024-diary-of-consumer-payment-choice/']
---
## Definition

The share of transactions (or sales value) settled by each payment method; POS reports group orders by payment method ([Lightspeed: built-in reports](https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom)). US benchmark: cash was 16% of all consumer payments in 2023 ([Federal Reserve: 2024 Diary of Consumer Payment Choice](https://www.frbservices.org/news/research/2024-diary-of-consumer-payment-choice/)).

## Business context

Payment mix supports decisions on card acceptance, cash handling and payment fees per franchise or country.

## Data usage

Source tables: samples.bakehouse.sales_transactions

count(DISTINCT transactionID) by paymentMethod / count(DISTINCT transactionID); value variant: sum(totalPrice) by paymentMethod / sum(totalPrice).
