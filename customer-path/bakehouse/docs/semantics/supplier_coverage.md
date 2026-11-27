---
term: Supplier Coverage
synonyms: [franchises per supplier, supplier reach]
domain: bakehouse_retail_sales
subdomain: franchise_supply
related_terms: [Supplier, Franchise, Approved Supplier]
sources: ['https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/']
---
## Definition

How many franchises each supplier serves; in a franchise system key suppliers are integral to the system ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)).

## Business context

Coverage shows supplier concentration risk: one supplier serving many franchises is a single point of failure for supply.

## Data usage

Source tables: samples.bakehouse.sales_franchises, samples.bakehouse.sales_suppliers

Proxy: count of franchises mapped to a supplier, not purchase volume (no purchase data).

count(DISTINCT franchiseID) by supplierID; also count(DISTINCT supplierID) with at least one franchise / count(supplierID).
