# Session 05 (wave 2): Metric View YAML Synthesis

Run `531733719859424`, branch `genie-build-bakehouse`, mode `edit` + `allow_execute`, continuation `0`. Domain `bakehouse_retail_sales`.

## Skills and inputs

* Session runner: the UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` could not be loaded by Genie Code (`readSkillFile` not found; the skill exists in UC). Used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
* Synthesis: UC skill `...ontology_mv_synthesis` likewise not loadable; used the SDK checkout fallback `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-mv-synthesis/SKILL.md` + `references/yaml-patterns.md`, plus the platform `metric-views` skill (`using-metric-views`, `joins-correctness.md`, `window-measures.md`, `materialization.md`).
* SDK: installed wheel `genie_ontology_modeled_knowledge_sdk-0.1.1` from `mbp/genie-ontology-modeled-knowledge-sdk/dist/` into the session's ephemeral Python env (not vendored).
* Inputs read: `sdk_config.json`, `PROJECT_MEMORY.md`, `docs/inputs_report.md`, `docs/plans/INDEX.md`, plan 05, `docs/research/02_kpi_definitions.md`, `docs/research/05_domain_subdomain_proposal.md`, glossary front matter in `docs/semantics/*.md` (synonyms), `docs/context/00_source_inventory.md` (no supplemental inputs, so no business-rule filters come from context), all four `docs/data_profiles/*.md` and `data_model_summary.md`.

## Metric views written

Folder `ontology-metric-views/metric_views/bakehouse_retail_sales/`:

| View | Subdomain | Grain / source | Joins (all `# verified:` from data_model_summary.md) |
|---|---|---|---|
| `mv_bakehouse_retail_sales_transactions` | sales | one row per POS transaction, `sales_transactions` (3333) | customer (many_to_one, orphan 0.0), franchise (many_to_one, orphan 0.0) -> nested supplier (one_to_one, orphan 0.4375; left join) |
| `mv_bakehouse_retail_sales_customer_activity` | customer | one row per registered customer (300); SQL source aggregating `sales_transactions` per customer with `sales_customers LEFT JOIN sales_transactions` (customerID many_to_one, keys unique) | none |
| `mv_bakehouse_retail_sales_supplier_coverage` | supply_network | one row per franchise store, `sales_franchises` (48) | supplier (one_to_one, orphan 0.4375; left join) |

All `source:` / `joins[].source` use `${source_catalog}.${source_schema}.<table>` only (the customer SQL source uses the same tokens). Excluded on purpose: `cardNumber` and customer personal data (names, email, phone, address, city, postal code), per `03_regulatory_context.md` / `05` owner question. The proposal's separate `mv_bakehouse_franchise_sales` was folded into the transactions view: its KPIs aggregate the same transaction grain (skill rule: one view per process and grain).

## KPI -> metric view mapping

| KPI (02_kpi_definitions) | Metric view | Measure |
|---|---|---|
| Gross Sales Revenue | transactions | Gross Sales Revenue |
| Transaction Count | transactions | Transaction Count (COUNT(1); transactionID unique) |
| Units Sold | transactions | Units Sold |
| Average Transaction Value | transactions | Average Transaction Value |
| Units per Transaction | transactions | Units per Transaction |
| Average Unit Price | transactions | Average Unit Price (constant 3) |
| Payment Mix Share | transactions | Payment Mix Share (window `range: all` over Payment Method) |
| Sales per Franchise | transactions | Sales per Franchise |
| Average Unit Volume | transactions | Average Unit Volume (Annualised) — proxy, extrapolated from the ~16.5-day window |
| Same-Store Sales Growth | transactions | Same-Store Sales Growth (Week over Week) — window `current` + `offset: -7 day` on Transaction Week; no YoY possible |
| Supplier Concentration | transactions | Supplier Sales Share (window `range: all` over Supplier Name) — sales-based proxy; count-based `Franchises per Supplier` in supplier_coverage is flat 1.0 |
| Active Customer Rate | customer_activity | Active Customer Rate |
| Revenue per Customer | customer_activity | Revenue per Customer |
| Purchase Frequency | customer_activity | Purchase Frequency |
| Repeat Purchase Rate | customer_activity | Repeat Purchase Rate |
| Customer Retention Rate | customer_activity | Customer Retention Rate — proxy: last 7 days of data vs the 7 days before |
| Customer Lifetime Value | customer_activity | Observed Customer Value (CLV Proxy) |
| Approved Supplier Rate | supplier_coverage | Approved Supplier Rate (All Franchises) and (Matched Suppliers) |
| Net Sales, Gross Margin | — | not computable (no discount/cost columns), per 02 |

## Owner decisions needed

* **Approved Supplier Rate basis.** Both exposed: (All Franchises) = franchises with approved supplier / all franchises, missing supplier row counts as not approved (27/48 = 0.5625; `data_model_summary.md` data-quality flag); (Matched Suppliers) = approved / franchises with a supplier row (1.0). Pick one canonical measure in tuning.
* **Customer Retention Rate periods.** Proxy uses rolling 7-day periods anchored on the latest transaction timestamp (296 prior-period customers, 292 retained). Alternative: calendar weeks.
* `Revenue per Customer` and `Observed Customer Value (CLV Proxy)` share a formula by design (02 defines the CLV proxy as observed revenue per customer).

## Materialization ranking

Thresholds from the skill (>= 10M rows, >= 3 joins, headline KPI). No table is >= 10M rows.

| View | Joins (incl. nested) | Source rows | Score | Headline KPI | Materialized |
|---|---|---|---|---|---|
| transactions | 3 | 3333 | 9999 | yes (revenue, ATV) | yes |
| supplier_coverage | 1 | 48 | 48 | no | no |
| customer_activity | 0 | 300 | 0 | no | no |

The transactions block: `mode: relaxed`, `every 6 hours`, one aggregated MV over categorical dims (Transaction Week, Product, Payment Method, Franchise Country) and the additive measures only (Gross Sales Revenue, Transaction Count, Units Sold), `refresh_policy: auto`, `cluster_by: {auto: true}`. Window measures were left out of the list on purpose. Note: EDA says materialization is optional at 3333 rows; if registration (wave 3) rejects the block in this workspace, removing it is a safe tuning change.

## Checks

| Check | Result |
|---|---|
| `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate metric_views` (from `ontology-metric-views/`) | pass: `3 file(s) checked: 0 error(s), 0 warning(s)`, exit 0 |
| `manifest.json` | written; content identical to `manifest.write_manifest(build_manifest(...))` output; sorted by name; lists all 3 YAMLs; `validate_manifest_json(entries, base_dir=<bundle root>)` returns `[]` |
| No literal catalog/schema/workspace values, no `$$` in YAML (MV004) | pass (scan of `source:` lines and for `samples.`, `hls_fde`, warehouse id, host) |
| `mv_yaml.render_ddl` with dev params leaves no `${` | pass, all 3 views |
| Read-only SQL cross-check of the expressions on `samples.bakehouse` | pass: revenue 66471 in both transactions and customer views; 3333 transactions; 300/300 active, 300 repeat customers; 296 prior-period, 292 retained; 1480 transactions under 'Unknown supplier' (matches EDA 44.4%); franchises 48, with supplier 27, approved 27, suppliers 27; 3 transaction weeks |
| `bundle validate --strict --target dev` ontology-metric-views | pass (Validation OK) |
| `bundle validate --strict --target dev` ontology-genie-agents | not passing, outside this session: `.rendered/ontology_agent.geniespace.json` does not exist. The agents are authored in wave 4 (session 08) and rendered from `docs/registration/resolved_target.json` (wave 3); no file of this session is involved |
| Platform dry run (scratch registration) | skipped: no `sql.ddl` authorization. Registration (wave 3) is the first platform check of nested join paths, window measures and the materialization block |

Manifest written through the workspace file tools with the exact SDK output (the session may not create workspace files from code), so `write_manifest` ran to `/tmp` and its output was copied.

## Files

* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_retail_sales_transactions.yml` (new)
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_retail_sales_customer_activity.yml` (new)
* `ontology-metric-views/metric_views/bakehouse_retail_sales/mv_bakehouse_retail_sales_supplier_coverage.yml` (new)
* `ontology-metric-views/metric_views/manifest.json` (new)

## Notes for later sessions

* 06 (registration): watch for `METRIC_VIEW_INVALID_VIEW_DEFINITION` on the materialization block and `UNRESOLVED_COLUMN` on nested paths (`franchise.supplier.*`). The customer view has a SQL source (no joins), so `cardinality_test` has nothing to compare there.
* 08 (curation): 3 views, one agent. Country labels differ: customer `USA` vs franchise `US`.
