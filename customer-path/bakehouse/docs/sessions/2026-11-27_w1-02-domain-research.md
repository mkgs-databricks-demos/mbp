# 2026-11-27 — Wave 1, Session 02: Domain Research & Glossary

* Build run: 38498872047824 (job 138308594859344, task `w1_session`), continuation 0, first attempt (no earlier status file for this run).
* Mode: `edit` + `allow_execute`. Workflow `hybrid`, branch `genie-build-bakehouse` (verified read-only via the Repos API, head `58183fd`). No Git commands run.

## What was done

1. Read PROJECT_MEMORY.md, sdk_config.json, docs/inputs_report.md, docs/plans/INDEX.md, plan 02 and the session 01 summary. No `hi_genie/` folder exists at the build root.
2. Skill: the UC skill could not be read by id (Genie Code cannot read UC skills yet), so the session used the workspace fallback `skills/ontology-domain-research/SKILL.md` in the SDK checkout.
3. Metadata read: one schema-scoped `information_schema.columns` query on the 4 source tables (42 columns, no column comments). No data scans.
4. Web research: **7 searches** (budget 10): retail terminology, franchise terminology, retail KPI formulas, bakery/QSR benchmarks, payment and privacy regulation, Databricks bakehouse sample dataset, comparable store sales definition.
5. Wrote 5 research docs and 23 glossary term files. Term content was rendered with `pages.write_terms` into a /tmp scratch folder (installed SDK wheel 0.1.1 from the SDK `sdk_wheels` volume into this session's scratch Python only), then written to the workspace with the workspace file tools (Python file writes into the Git folder are not allowed by the tool policy). That took 2 tool calls per file instead of one `write_terms` call.

## Decisions

* **File names follow plan 02, not the skill.** The plan names `01_terminology.md` and `04_benchmarks.md`; the skill names `01_domain_overview.md` and `04_industry_benchmarks.md`. The manifest scope says only "docs/research/01-05", and the wave gate checks the 01-04 prefixes, so I used the plan names. `01_terminology.md` also covers the skill's domain overview content.
* Subdomains: `sales` (sales_transactions), `customers` (sales_customers), `franchise_supply` (sales_suppliers). `sales_franchises` is a shared dimension with home `sales`.
* Gross Sales = sum(totalPrice). Net Sales is `not computable` (no returns or discounts). Proxies: Comparable Franchise Sales Growth (franchises with sales in both periods; there is no opening date), Customer Coverage, Supplier Coverage. Each proxy term file has a `Proxy:` line.
* Coded columns are deferred to EDA (`## Values from EDA`): paymentMethod, product, sales_franchises.size, sales_suppliers.size/ingredient/approved, sales_customers.gender.
* Sensitive data: `cardNumber` (PCI DSS v4.0.1) and customer contact fields (CCPA/GDPR) are documented as excluded from all models (`cardholder_data.md`, `03_regulatory_context.md`).

## Files modified

* `docs/research/01_terminology.md`, `02_kpi_definitions.md`, `03_regulatory_context.md`, `04_benchmarks.md`, `05_domain_subdomain_proposal.md` (created)
* `docs/semantics/`: approved_supplier, average_transaction_value, cardholder_data, comparable_franchise_sales, customer, customer_coverage, franchise, gross_sales, net_sales, payment_method, payment_method_mix, product, product_mix, purchase_frequency, repeat_customer_rate, revenue_per_customer, sales_per_franchise, sales_transaction, supplier, supplier_coverage, unit_price, units_per_transaction, units_sold (`.md`, created)

## Checks

| Check | Result | Detail |
|---|---|---|
| research docs 01-05 exist with URLs | pass | each has a `## Sources` section; https links in Sources: 9 / 12 / 7 / 5 / 3 |
| parse_glossary('docs/semantics') | pass | 23 of 23 term files parsed; workspace files are byte-identical to the write_terms render |
| glossary contract | pass | domain = bakehouse_retail_sales on all files; subdomains in {sales, customers, franchise_supply}; every related_term has a term file |
| no workspace-specific identifiers | pass | scanned all 28 files for catalog, user, warehouse and domain ids: none |
| web search budget | pass | 7 of 10 |
| 05 table assignment | pass | 4 source tables: 3 assigned to one subdomain each, 1 shared with a home subdomain |

## Notes for later sessions

* Session 04 (EDA): please confirm the sales_transactions row grain, whether totalPrice = quantity * unitPrice, the dateTime span (comparable sales needs more than one period) and the coded values listed above.
* Session 05 (MV synthesis): use the KPI names and formulas in `02_kpi_definitions.md`; keep `(proxy)` in the names of proxy measures; never expose cardNumber or customer contact columns.
* Owner: the currency of price columns is not recorded; the open questions are in 03 (gender, postal_zip_code exposure).

## Requests

None.
