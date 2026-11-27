---
term: Customer
synonyms: [buyer, shopper, guest]
domain: bakehouse_retail_sales
subdomain: customers
related_terms: [Revenue per Customer, Purchase Frequency, Repeat Customer Rate, Customer Coverage]
sources: ['https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf', 'https://cppa.ca.gov/regulations/consumer_privacy_act']
---
## Definition

The party to a retail transaction ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)). Names, emails and addresses that identify a customer are personal information under California privacy law ([CPPA: CCPA Regulations](https://cppa.ca.gov/regulations/consumer_privacy_act)).

## Business context

Customers are analysed by geography and segment to understand reach and loyalty; their contact fields are personal data and must not be exposed in analytics.

## Data usage

Source tables: samples.bakehouse.sales_customers, samples.bakehouse.sales_transactions

Key `customerID` (join sales_transactions.customerID = sales_customers.customerID); analytic attributes city, state, country, continent, gender. Do not expose first_name, last_name, email_address, phone_number or address.

## Values from EDA

values_from_eda: true

Columns: sales_customers.gender (observed codes are listed by the deep EDA stage).
