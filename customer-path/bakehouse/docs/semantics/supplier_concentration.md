---
term: Supplier Concentration
synonyms: [supplier dependency]
domain: bakehouse_retail_sales
subdomain: supply_network
related_terms: [Supplier, Approved Supplier Rate]
sources: ['https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html']
---
## Definition

Share of supply that depends on the top supplier or suppliers; a source of system risk in franchise supply chains ([Franchising.com](https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html)).

## Business context

Used for supply-risk and negotiation decisions.

## Data usage

Source tables: samples.bakehouse.sales_franchises, samples.bakehouse.sales_suppliers, samples.bakehouse.sales_transactions

Proxy: share of franchises (or of franchise sales) served by the top N suppliers, not purchase spend; there is no spend data.

count(franchiseID) per supplierID / count(franchiseID).
