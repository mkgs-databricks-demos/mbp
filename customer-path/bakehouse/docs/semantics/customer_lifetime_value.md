---
term: Customer Lifetime Value
synonyms: [CLV, LTV]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Revenue per Customer, Purchase Frequency]
sources: ['https://blog.hubspot.com/service/how-to-calculate-customer-lifetime-value']
---
## Definition

Average purchase value x purchase frequency x customer lifespan ([HubSpot](https://blog.hubspot.com/service/how-to-calculate-customer-lifetime-value)).

## Business context

Guides how much to spend on acquiring and keeping customers.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Proxy: observed customer value, i.e. revenue per customer over the observed window; there is no lifespan data.

sum(totalPrice) / count(distinct customerID) over the full window.
