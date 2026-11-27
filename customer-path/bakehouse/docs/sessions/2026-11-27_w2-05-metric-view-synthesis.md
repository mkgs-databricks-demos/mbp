# 2026-11-27 — Wave 2, Session 05: Metric View YAML Synthesis

* Build run: 38498872047824 (job 138308594859344, task `w2_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute`. Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` confirmed on that branch with a read-only `git rev-parse`; no Git commands that change state).

## What was done

1. Skills: the UC skill ids (`hls_fde_dev.dev_matthew_giglia_ontology_sdk.*`) did not resolve through `readSkillFile`, so the workspace fallbacks were used: session runner from `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`, and `ontology-mv-synthesis` (+ `references/yaml-patterns.md`) from the SDK checkout `mbp/genie-ontology-modeled-knowledge-sdk/skills/`. Platform `metric-views` skill, `joins-correctness.md`, `semantic-metadata.md` and `window-measures.md` loaded.
2. Inputs read: `sdk_config.json`, `PROJECT_MEMORY.md`, `docs/inputs_report.md` (via session 04 summary), `docs/research/02_kpi_definitions.md`, `03_regulatory_context.md`, `05_domain_subdomain_proposal.md`, glossary front matter in `docs/semantics/*.md` (synonyms), `docs/context/00_source_inventory.md` (no supplemental inputs), all four `docs/data_profiles/*.md` and `data_model_summary.md`.
3. Wrote three metric view YAMLs and `manifest.json` (below). SDK wheel `genie_ontology_modeled_knowledge_sdk-0.1.1` installed from the SDK checkout `dist/` into the session's serverless Python env (not into the project) to run the validator and manifest functions.
4. Read-only SQL only: per-day franchise activity (all 46-48 franchises sell every day, informs the comparable-sales proxy) and plain-SQL cross-checks of the customer SQL source (300 customers, 300 buyers, 300 repeaters, gross sales 66471, 3333 transactions) and of franchise -> supplier coverage (48 franchises, 27 with supplier, 27 distinct suppliers, 27 approved).

## Metric views

| view | subdomain | grain / source | joins | measures | dimensions |
|---|---|---|---|---|---|
| `mv_bakehouse_sales` | sales | one row per transaction, `sales_transactions` | `franchise` (many_to_one, orphan 0.0), `customer` (many_to_one, orphan 0.0) | 18 | 14 |
| `mv_bakehouse_customer_activity` | customers | one row per customer: SQL source `sales_customers` LEFT JOIN per-customer aggregate of `sales_transactions` | none (join inside SQL source) | 9 | 8 |
| `mv_bakehouse_supplier_coverage` | franchise_supply | one row per franchise, `sales_franchises` | `supplier` (one_to_one on matched keys, orphan 0.4375; left outer) | 9 | 11 |

Every join carries a `# verified:` line copied from the `data_model_summary.md` row, `cardinality: many_to_one` and `rely.at_most_one_match: true`. `sales_franchises -> sales_suppliers` was not added to `mv_bakehouse_sales`: no KPI needs supplier attributes at transaction grain (the data has no ingredient-to-product link), and the 3-table `multi_join` signal was marked pending by session 04.

## KPI -> metric view mapping

| KPI (02_kpi_definitions.md) | metric view | measure |
|---|---|---|
| Gross Sales | mv_bakehouse_sales | `Gross Sales` |
| Net Sales | — | not modeled: not computable (no returns, allowances or discounts); stated in the view comment |
| Units Sold | mv_bakehouse_sales | `Units Sold` |
| Transaction Count | mv_bakehouse_sales | `Transaction Count` (COUNT(1); equals COUNT(DISTINCT transactionID), PK verified unique) |
| Average Transaction Value | mv_bakehouse_sales | `Average Transaction Value` |
| Units per Transaction | mv_bakehouse_sales | `Units per Transaction` |
| Average Selling Price | mv_bakehouse_sales | `Average Selling Price` (constant 3 in the data; comment says so) |
| Product Mix | mv_bakehouse_sales | `Product Mix` (window-measure denominator `Gross Sales All Products`, range all over Product) |
| Payment Method Mix | mv_bakehouse_sales | `Payment Method Mix` (window denominator `Transaction Count All Payment Methods`) |
| Sales per Franchise | mv_bakehouse_sales | `Sales per Franchise` (helper `Franchises with Sales`) |
| Comparable Franchise Sales Growth | mv_bakehouse_sales | `Comparable Franchise Sales Growth (proxy)`: day-over-day, `Daily Gross Sales` / `Prior Day Gross Sales` window measures (range current, offset -1 day) |
| Revenue per Customer | mv_bakehouse_customer_activity | `Revenue per Customer` |
| Purchase Frequency | mv_bakehouse_customer_activity | `Purchase Frequency` |
| Repeat Customer Rate | mv_bakehouse_customer_activity | `Repeat Customer Rate` |
| Customer Coverage | mv_bakehouse_customer_activity | `Customer Coverage (proxy)` |
| Supplier Coverage | mv_bakehouse_supplier_coverage | `Supplier Coverage (proxy)` (franchise basis) and `Franchises per Supplier` (supplier basis) |
| Approved Supplier Share | mv_bakehouse_supplier_coverage | `Approved Supplier Share (Supplier Basis)` and `Approved Supplier Share (Franchise Basis)` |

## Decisions

* **Franchise sales folded into `mv_bakehouse_sales`.** The research proposal listed a separate `mv_bakehouse_franchise_sales`, but Sales per Franchise and the comparable-sales proxy aggregate the same transaction grain as the other sales KPIs; the skill rule is one view per business process and grain. Franchise slicing is available through the `franchise` join.
* **View names** follow the research proposal (`mv_bakehouse_<process>`) rather than the literal `mv_<domain_name>_<process>` (`mv_bakehouse_retail_sales_...`), to keep the names session 02 published in the proposal and glossary. Folder = domain `bakehouse_retail_sales`.
* **Customer view uses a SQL source** (customer grain with per-customer totals) so Customer Coverage and Repeat Customer Rate are computed over known customers without fan-out. Consequence: customer KPIs are over the full data span, not time-sliceable (stated in the view comment). All customers buy and repeat in the current data, so coverage and repeat rate are 1.0.
* **Comparable sales proxy at day grain**: the data spans 17 days, so week/month comparisons have 2-3 partial points. The proxy is only comparable when grouped by `Franchise ID`; stated in the comment.
* **Excluded fields** (03_regulatory_context.md + EDA): `cardNumber`; customer first/last name, email, phone, address, city, postal code. `Customer Gender` is exposed as an aggregated dimension with "owner decision pending" in its comment.
* **No currency format**: currency is not stated in the data, so monetary measures use number format (2 decimals on ratios) rather than `currency: USD`.
* **Country naming** (`US` for stores vs `USA` for customers) documented in both dimension comments; not normalized.

## Owner decisions needed (two-formula KPIs)

* **Supplier Coverage**: research gives `count(DISTINCT franchiseID) by supplierID` (franchises per supplier) or `suppliers with franchises / all suppliers`. Exposed: `Supplier Coverage (proxy)` = franchises with a supplier on file / all franchises (0.5625), and `Franchises per Supplier` (1.0). The "suppliers with franchises / all suppliers" basis is 27/27 = 1.0 and needs a supplier-grain source, so it is not modeled.
* **Approved Supplier Share**: `approved suppliers / all suppliers` vs `franchises on approved suppliers / all franchises`. Both exposed: `(Supplier Basis)` = 1.0, `(Franchise Basis)` = 0.5625.
* **Customer Gender** exposure (aggregated only) — confirm or remove.

## Materialization ranking

Thresholds from the skill (no thresholds stated in the profiles): >= 10M source rows, >= 3 joins, or a headline/dashboard KPI flagged in research/context.

| view | joins | source rows | score (joins x rows) | threshold met | materialized |
|---|---|---|---|---|---|
| mv_bakehouse_sales | 2 | 3333 | 6666 | no (2 joins; research marks no headline KPI; no context docs) | no |
| mv_bakehouse_supplier_coverage | 1 | 48 | 48 | no | no |
| mv_bakehouse_customer_activity | 0 (SQL source) | 300 | 0 | no | no |

No materialization blocks. The EDA `hot_table` flag on `sales_transactions` was marked "optional; flag only" (3333 rows).

## Checks

| check | result | detail |
|---|---|---|
| `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate metric_views` (from bundle root, wheel 0.1.1) | pass | `3 file(s) checked: 0 error(s), 0 warning(s)`, exit 0 |
| `manifest.validate_manifest_json(manifest, base_dir=bundle root)` | pass | `[]`; `build_manifest` output equals the committed file; JSON array sorted by name; lists all 3 `*.yml` |
| `manifest.write_manifest` | pass | written to a scratch copy (`/tmp`), byte-identical to the workspace `manifest.json` (workspace file written with the file tools, per session rules) |
| no literal catalogs/schemas/workspace values (MV004) | pass | no `samples.`, `hls_fde`, warehouse id or 3-part literal reference in any YAML; no `$$` |
| `mv_yaml.render_ddl` with dev params | pass | no `${` left in rendered DDL for any view |
| plain-SQL cross-check of customer SQL source and supplier coverage | pass | values above |
| `bundle validate --strict --target dev` (ontology-metric-views) | pass | `Validation OK!` |
| platform dry run (scratch registration) | skipped | no `sql.ddl` authorization; registration (session 06) is the first platform check |

## Files modified

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml` (created)
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml` (created)
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml` (created)
* `ontology-metric-views/metric_views/manifest.json` (created)

## Notes for later sessions

* 06 (registration): watch for platform-only errors on the window measures (`Product Mix` / `Payment Method Mix` denominators with `range: all` over string dimensions; `Prior Day Gross Sales` with `offset: -1 day` on a `CAST(... AS DATE)` order dimension) and the SQL source of `mv_bakehouse_customer_activity`. The cardinality test has 3 joins to check (2 in sales, 1 in supplier coverage).
* 08 (agent curation): 3 views, one agent (well under 30). Subdomains: sales, customers, franchise_supply.

## Requests

None. Owner note: the UC skill ids in `sdk_config.json` `skills` still do not resolve through `readSkillFile`; workspace fallbacks were used.
