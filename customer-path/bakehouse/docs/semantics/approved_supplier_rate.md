---
term: Approved Supplier Rate
synonyms: [approved supplier coverage]
domain: bakehouse_retail_sales
subdomain: supply_network
related_terms: [Supplier, Supplier Concentration]
sources: ['https://www.fooddocs.com/food-safety-templates/approved-supplier-list']
---
## Definition

Share of franchises supplied by a supplier on the approved supplier list. That list is the register of suppliers vetted and authorised for procurement ([FoodDocs](https://www.fooddocs.com/food-safety-templates/approved-supplier-list)).

## Business context

A food-safety and compliance indicator for the franchise supply chain.

## Data usage

Source tables: samples.bakehouse.sales_franchises, samples.bakehouse.sales_suppliers

count(franchises whose supplier is approved) / count(franchises); the meaning of the approved codes is pending EDA.

## Values from EDA

values_from_eda: true

Column: sales_suppliers.approved
