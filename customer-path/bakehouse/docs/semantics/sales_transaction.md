---
term: Sales Transaction
synonyms: [transaction, sale, ticket, receipt]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Product, Gross Sales, Payment Method, Average Transaction Value]
sources: ['https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf']
---
## Definition

A record of business conducted between a retail store and a customer involving the exchange of merchandise for tender ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)).

## Business context

The transaction is the base event for every sales KPI: revenue, units, basket and payment mix are all aggregated from it. Store managers and the franchisor use transaction counts to track traffic.

## Data usage

Source tables: samples.bakehouse.sales_transactions

One transaction is identified by `transactionID`; it links to a customer (`customerID`), a franchise (`franchiseID`) and a timestamp (`dateTime`). Count with count(DISTINCT transactionID). Grain of a row (one product line per transactionID, or one row per transaction) is confirmed by the deep EDA stage (docs/data_profiles/).
