# 05 Domain / Subdomain Proposal — bakehouse_retail_sales

## Proposed domain
* Name: bakehouse_retail_sales
* Description: Point-of-sale sales of a franchised bakery chain, with its customers, franchise stores and ingredient suppliers.

## Subdomains
| subdomain | description | source tables | candidate metric views | glossary terms |
|---|---|---|---|---|
| sales | POS transaction performance: revenue, units, ticket, basket, product and payment mix, store sales | samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises (shared) | mv_bakehouse_sales_transactions, mv_bakehouse_franchise_sales | Gross Sales Revenue, Transaction Count, Units Sold, Average Transaction Value, Units per Transaction, Average Unit Price, Payment Mix Share, Payment Method, Product, Sales per Franchise, Average Unit Volume, Same-Store Sales Growth, Franchise, POS Transaction |
| customer | Customer coverage and behaviour: active, repeat, retention, frequency, value | samples.bakehouse.sales_customers, samples.bakehouse.sales_franchises (shared) | mv_bakehouse_customer_activity | Customer, Active Customer Rate, Revenue per Customer, Purchase Frequency, Repeat Purchase Rate, Customer Retention Rate, Customer Lifetime Value |
| supply_network | Franchise-to-supplier coverage: approved suppliers, ingredient sourcing, concentration | samples.bakehouse.sales_suppliers, samples.bakehouse.sales_franchises (shared) | mv_bakehouse_supplier_coverage | Supplier, Approved Supplier Rate, Supplier Concentration |

## Shared dimensions
| table | used by subdomains | home subdomain (tie-break) |
|---|---|---|
| samples.bakehouse.sales_franchises | sales, customer, supply_network | sales |

Tie-break: 6 KPIs in `02` need `sales_franchises`. Sales per Franchise, Average Unit Volume and Same-Store Sales Growth are `sales`. Approved Supplier Rate and Supplier Concentration are `supply_network`. Revenue by franchise geography for customer KPIs is `customer`. With 3 of the 6, `sales` uses it most, so its home is `sales`.

## Rationale
* The split follows the three business processes in the domain context: selling, customer coverage and supplier coverage ([01 Domain Overview](01_domain_overview.md); [Kimball: Grain](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/)).
* `sales_franchises` is a conformed dimension. It joins transactions (by `franchiseID`) and suppliers (by `supplierID`), so it is shared rather than duplicated ([Kimball: Conformed Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/conformed-dimension/)).
* `sales_transactions` is the only fact table, and all customer KPIs derive from it. Customer KPIs still form their own subdomain because their grain is customer x period, not transaction ([02 KPI Definitions](02_kpi_definitions.md)).
* The candidate view count is about 4, well under `max_metric_views_per_agent` (30). One Genie Agent covering all subdomains is expected (PROJECT_MEMORY decision 1).

## Alternatives considered
* **Single subdomain `sales`.** This is simpler, but supplier coverage would be hidden inside sales, and supplier coverage is a separate process with its own grain ([FoodDocs: Approved Suppliers List](https://www.fooddocs.com/food-safety-templates/approved-supplier-list)).
* **Put customer KPIs under `sales`.** This is plausible because they come from the same fact table. Rejected so that customer-grain measures (retention, repeat rate) are not mixed with transaction-grain measures.

## Owner decisions needed
* [ ] Create the domain and subdomains in UC (opt-in)
* [ ] Confirm that `cardNumber` and customer personal-data columns stay out of every metric view (see [03 Regulatory Context](03_regulatory_context.md))

## Sources
1. [Grain](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/) — Kimball Group
2. [Conformed Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/conformed-dimension/) — Kimball Group
3. [Approved Suppliers List](https://www.fooddocs.com/food-safety-templates/approved-supplier-list) — FoodDocs
4. [Seizing an Opportunity: Supplier Contracts and System Health](https://www.franchising.com/amp/articles/seizing_an_opportunity_supplier_contracts_and_system_health.html) — Franchising.com
