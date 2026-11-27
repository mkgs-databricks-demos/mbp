---
term: Sales per Franchise
synonyms: [sales per store, store sales]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Franchise, Average Unit Volume]
sources: ['https://retail-support.lightspeedhq.com/hc/en-us/articles/4410640218523-Navigating-Lightspeed-Analytics']
---
## Definition

Total sales divided by the number of stores in the period ([Lightspeed](https://retail-support.lightspeedhq.com/hc/en-us/articles/4410640218523-Navigating-Lightspeed-Analytics)).

## Business context

Compares store productivity across the system.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises

sum(totalPrice) / count(distinct franchiseID).
