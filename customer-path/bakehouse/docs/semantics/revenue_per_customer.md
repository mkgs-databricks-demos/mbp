---
term: Revenue per Customer
synonyms: [average revenue per customer, ARPC, spend per customer]
domain: bakehouse_retail_sales
subdomain: customers
related_terms: [Customer, Gross Sales, Purchase Frequency]
sources: ['https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom']
---
## Definition

Total revenue divided by the number of customers ([Lightspeed: built-in reports](https://x-series-support.lightspeedhq.com/hc/en-us/articles/41595804486171-Understanding-built-in-reports-in-Lightspeed-eCom)).

## Business context

Revenue per customer measures customer value and helps target loyalty programs.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) / count(DISTINCT customerID) over the period.
