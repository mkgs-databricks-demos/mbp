---
term: Customer Retention Rate
synonyms: [CRR, retention rate]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Repeat Purchase Rate, Customer]
sources: ['https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/']
---
## Definition

((customers at end of period minus new customers) / customers at start of period) x 100 ([Salesforce](https://www.salesforce.com/service/digital-customer-engagement-platform/customer-retention-rate/)).

## Business context

A core loyalty KPI.

## Data usage

Source tables: samples.bakehouse.sales_transactions

Proxy: buying customers in both the prior and the current period / buying customers in the prior period; there is no customer start date.

Computed from customerID and dateTime by period.
