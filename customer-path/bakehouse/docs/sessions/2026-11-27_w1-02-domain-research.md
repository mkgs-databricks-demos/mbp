# 2026-11-27 — Wave 1, Session 02: Domain Research & Glossary

Run `531733719859424`, mode `edit` (allow_execute), workflow `hybrid`, branch `genie-build-bakehouse` (verified read-only via Repos API). Continuation `0`, no earlier status file, so this was a fresh run.

## What was done

* Skill loading: the runner UC skill and the `ontology-domain-research` UC skill could not be loaded by UC id. Used the documented fallbacks: `genie-build-waves/src/skills/genie-build-session-runner/SKILL.md` and `skills/ontology-domain-research/SKILL.md` in the SDK checkout.
* Metadata: ran one schema-scoped `information_schema.columns` query for the 4 source tables (42 columns, none with comments). The table comment states the dataset is a synthetic sample. No data scans.
* Web searches: **7 of 10** budget (terminology, KPI formulas, customer/supplier KPIs, regulation, benchmarks, dataset provenance, dimensional modelling + GDPR). Stopped by rule 2: 01-04 each have at least 3 sources and there are more than 10 terms.
* Wrote research docs `docs/research/01_domain_overview.md`, `02_kpi_definitions.md` (20 KPIs with formula, numerator, denominator, grain, time_period, source, candidate_tables, proxy), `03_regulatory_context.md`, `04_industry_benchmarks.md` (`not found` where no source exists) and `05_domain_subdomain_proposal.md`.
* Wrote 24 glossary term files in `docs/semantics/` in one `pages.write_terms` call, using installed SDK wheel `0.1.1` from the SDK checkout `dist/`.

## Decisions

* **Subdomains:** `sales` (sales_transactions), `customer` (sales_customers), `supply_network` (sales_suppliers). `sales_franchises` is a shared dimension with home `sales` (tie-break: it is used by 3 of the 6 franchise-dependent KPIs). About 4 candidate views, far under the limit of 30, so one agent.
* **Proxy KPIs** (each has a `Proxy:` line): Average Unit Volume (annualised), Customer Retention Rate (purchase-based), Customer Lifetime Value (observed value), Supplier Concentration (franchise count, not spend). Net Sales and Gross Margin are `not computable`.
* **Coded columns deferred to EDA** (`## Values from EDA`): paymentMethod, product, franchise `size`, supplier `approved`/`size`/`ingredient`, customer `gender`. No code meanings were guessed.
* **Privacy:** 03 recommends keeping `cardNumber` (PCI DSS v4.0.1) and customer direct identifiers (GDPR/CCPA) out of every metric view. These are listed as owner decisions in 05.

## Conflicts noted

* Plan 02 names `01_terminology.md` and `04_benchmarks.md`. The skill's output contract (and checklist) names `01_domain_overview.md` and `04_industry_benchmarks.md`. The manifest scope says only "docs/research/01-05". I followed the skill names, which satisfy the wave gate ("01-04 research docs plus 05").
* The CCPA citation points to the California Legislative Information site root; the exact section URL was not retrieved.

## Checks

| Check | Result |
|---|---|
| Research docs 01-05 exist, each with `## Sources` and https links (17/17/11/7/4) | pass |
| 02 has `formula` and `proxy` columns; 04 uses `not found` (8 rows) | pass |
| 05 places all 4 source tables (franchises as shared) | pass |
| `pages.parse_glossary('docs/semantics')` parses all 24 files | pass |
| Independent read-back: every term file has the front matter keys, `domain: bakehouse_retail_sales`, a source URL, 3 sections and a `Source tables:` line | pass (0 issues) |
| Proxy KPIs have a `Proxy:` line (4 files) | pass |
| No workspace identifiers (user, host, catalog, warehouse or page ids) in research or semantics files | pass |
| Web searches ≤ 10 (7 used) | pass |
| No Git commands, no file deletions | pass |

## Files created

* `docs/research/01_domain_overview.md`, `02_kpi_definitions.md`, `03_regulatory_context.md`, `04_industry_benchmarks.md`, `05_domain_subdomain_proposal.md`
* `docs/semantics/`: 24 term files (see the status file for the list)

## Notes for later sessions

* Session 04 (EDA): confirm that `transactionID` is unique per row, that `totalPrice = quantity * unitPrice`, the price currency, the `dateTime` range, and the observed values of the coded columns listed above.
* Session 05 (MV synthesis): use ratio-of-sums measures, label proxy measures as approximations, and exclude `cardNumber` and customer PII columns.

## Requests

None.
