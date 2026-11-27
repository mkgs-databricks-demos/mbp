# 05 Domain / Subdomain Proposal — bakehouse_retail_sales

## Proposed domain
* Name: bakehouse_retail_sales
* Description: Retail franchise sales of baked goods: revenue, units, basket and payment mix by product, franchise and geography, plus customer and supplier coverage.

## Subdomains
| subdomain | description | source tables | candidate metric views | glossary terms |
|---|---|---|---|---|
| sales | Transactions, products, revenue, basket, payment mix and franchise sales performance | samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises (shared) | mv_bakehouse_sales (gross sales, units, transactions, ATV, UPT, average selling price, product mix, payment method mix), mv_bakehouse_franchise_sales (sales per franchise, comparable franchise sales growth proxy) | Sales Transaction, Product, Units Sold, Unit Price, Gross Sales, Net Sales, Average Transaction Value, Units per Transaction, Payment Method, Payment Method Mix, Product Mix, Sales per Franchise, Comparable Franchise Sales, Cardholder Data |
| customers | Customer base, geography and purchase behaviour | samples.bakehouse.sales_customers | mv_bakehouse_customer_activity (revenue per customer, purchase frequency, repeat customer rate, customer coverage) | Bakehouse Customer, Revenue per Customer, Purchase Frequency, Repeat Customer Rate, Customer Coverage |
| franchise_supply | Franchise network and ingredient suppliers | samples.bakehouse.sales_suppliers, samples.bakehouse.sales_franchises (shared) | mv_bakehouse_supplier_coverage (franchises per supplier, approved supplier share) | Franchise, Bakehouse Supplier, Approved Supplier, Supplier Coverage |

## Shared dimensions
| table | used by subdomains | home subdomain (tie-break) |
|---|---|---|
| samples.bakehouse.sales_franchises | sales, franchise_supply | sales |

Tie-break: in `02_kpi_definitions.md`, sales KPIs that need sales_franchises (Sales per Franchise, Comparable Franchise Sales Growth, plus franchise/city/country slicing of every sales KPI) outnumber franchise_supply KPIs (Supplier Coverage, Approved Supplier Share), so the home is `sales`.

Table assignment: sales_transactions -> sales; sales_customers -> customers; sales_suppliers -> franchise_supply; sales_franchises -> shared (home sales). Every source table from `sdk_config.json` is assigned exactly once.

## Rationale
* The split follows the standard retail model of transactions/tenders, customers and stores ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)) and the franchising view of locations and key suppliers ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)); see `01_terminology.md` and `02_kpi_definitions.md`.
* Customer KPIs use a different denominator (customers) from sales KPIs (transactions), so a separate subdomain keeps measure definitions clear.
* About 4-5 metric views in total, well below `max_metric_views_per_agent` (30), so one Genie Agent covers the whole domain (Decision 1 in PROJECT_MEMORY.md).

## Alternatives considered
* One `sales` subdomain for everything: simpler, but mixes supplier coverage (a network snapshot) with transactional KPIs and hides the supply-chain audience.
* A separate `geography` subdomain: rejected; city/country are attributes of franchises and customers, not a business process.

## Owner decisions needed
* [ ] Create the domain and subdomains in UC (opt-in)
* [ ] Confirm excluding cardNumber and customer contact fields from all models (see `03_regulatory_context.md`)

## Sources
1. [Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf) — Oracle
2. [IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/) — International Franchise Association
3. [Shopify Help Center: Analytics fields](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/analytics-fields) — Shopify
