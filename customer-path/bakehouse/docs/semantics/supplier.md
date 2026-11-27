---
term: Supplier
synonyms: [vendor, ingredient supplier, key supplier]
domain: bakehouse_retail_sales
subdomain: franchise_supply
related_terms: [Approved Supplier, Franchise, Supplier Coverage]
sources: ['https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/']
---
## Definition

A key supplier or vendor is one with whom the franchisor has negotiated pricing or product availability and whose products are integral to the franchise system ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)).

## Business context

Each franchise sources ingredients from one supplier, so supplier quality and location affect every franchise it serves.

## Data usage

Source tables: samples.bakehouse.sales_suppliers, samples.bakehouse.sales_franchises

Key `supplierID` (join sales_franchises.supplierID = sales_suppliers.supplierID); attributes name, ingredient, continent, city, district, size, latitude, longitude, approved.

## Values from EDA

values_from_eda: true

Columns: sales_suppliers.size, sales_suppliers.ingredient (observed values are listed by the deep EDA stage).
