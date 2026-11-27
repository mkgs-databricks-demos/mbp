---
term: Supplier
synonyms: [vendor, ingredient supplier]
domain: bakehouse_retail_sales
subdomain: supply_network
related_terms: [Approved Supplier Rate, Franchise]
sources: ['https://www.fooddocs.com/food-safety-templates/approved-supplier-list', 'https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html']
---
## Definition

A vendor that provides ingredients to franchises. Franchise systems often require purchases from approved suppliers ([Franchising.com](https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html)).

## Business context

Each franchise sources from one supplier, so supplier quality and approval affect the whole system ([FoodDocs](https://www.fooddocs.com/food-safety-templates/approved-supplier-list)).

## Data usage

Source tables: samples.bakehouse.sales_suppliers, samples.bakehouse.sales_franchises

Dimension keyed by supplierID; attributes ingredient, continent, size, approved.

## Values from EDA

values_from_eda: true

Columns: sales_suppliers.approved, sales_suppliers.size, sales_suppliers.ingredient
