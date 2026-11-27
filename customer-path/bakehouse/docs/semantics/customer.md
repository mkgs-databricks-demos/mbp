---
term: Customer
synonyms: [buyer, guest, shopper]
domain: bakehouse_retail_sales
subdomain: customer
related_terms: [Active Customer Rate, Revenue per Customer]
sources: ['https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/', 'https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/eng/pdf']
---
## Definition

A person who buys from the franchise system. Customer records are personal data under GDPR Article 4(1) ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/eng/pdf)).

## Business context

The base for retention and frequency analysis ([Salesforce](https://www.salesforce.com/eu/service/digital-customer-engagement-platform/customer-retention/)). Use only customerID and geography; exclude names, email, phone and address.

## Data usage

Source tables: samples.bakehouse.sales_customers

Dimension keyed by customerID; joins samples.bakehouse.sales_transactions.customerID.

## Values from EDA

values_from_eda: true

Column: sales_customers.gender
