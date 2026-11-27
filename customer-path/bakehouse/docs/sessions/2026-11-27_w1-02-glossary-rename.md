# 2026-11-27 — Wave 1, Session 02: Domain Research & Glossary (glossary rename re-run)

* Build run: 244030216249267 (job 138308594859344, task `w1_session`), continuation 0, first attempt for this run.
* Mode: `edit` + `allow_execute`. Workflow `hybrid`, branch `genie-build-bakehouse` (verified read-only via the Repos API, head `da8098c`). No Git commands run.
* Status: **blocked** (one file deletion was refused; see below).

## Problem

Session 02 already passed in build run 38498872047824 (see `2026-11-27_w1-02-domain-research.md`). Since then `sdk_config.json` `domain_context` was changed by the owner: the shared Discover domain already has TPC-H pages titled Customer and Supplier, so the glossary must name these entities **Bakehouse Customer** and **Bakehouse Supplier** (files `bakehouse_customer.md` and `bakehouse_supplier.md`, replacing `customer.md` and `supplier.md`, and in every `related_terms` list). All other term names stay unchanged.

## What was done

1. Read the session runner skill (workspace fallback; the UC skill id could not be read), `waves.json`, `sdk_config.json`, `PROJECT_MEMORY.md`, `docs/inputs_report.md`, plan 02 and the previous session 02 summary. No `hi_genie/` folder at the build root.
2. Research content was not redone: the earlier research docs and term content remain valid. Only the rename was applied. No web searches, no table reads.
3. Created `docs/semantics/bakehouse_customer.md` (term `Bakehouse Customer`) and `docs/semantics/bakehouse_supplier.md` (term `Bakehouse Supplier`), body copied unchanged from the old files.
4. Updated `related_terms` in 8 files: approved_supplier, cardholder_data, customer_coverage, franchise, purchase_frequency, repeat_customer_rate, revenue_per_customer, supplier_coverage.
5. Updated the glossary-terms column of `docs/research/05_domain_subdomain_proposal.md` (customers and franchise_supply rows).
6. Moved `docs/semantics/supplier.md` to the workspace Trash.
7. Moving `docs/semantics/customer.md` to Trash was **refused** by the Auto Mode approval check (deletion not explicitly authorized). Not retried, not worked around.

## Decisions

* `01_terminology.md` row "Customer" (Finding column) and `02_kpi_definitions.md` "Customer KPIs" are generic concept labels, not glossary term names, so they were left unchanged.
* Synonyms of the renamed terms were kept as they were (no `customer` / `supplier` synonyms, to avoid colliding with the TPC-H pages).

## Checks

| Check | Result | Detail |
|---|---|---|
| parse_glossary('docs/semantics') | pass | 24 of 24 files parsed (installed SDK wheel 0.1.1, scratch Python only); no duplicate term names |
| related_terms resolve | pass | every related_term has a term file; no related_terms list names bare Customer or Supplier |
| rename per domain_context | fail | `customer.md` (term `Customer`) still exists; it would publish a page that collides with the TPC-H Customer page |
| research docs 01-05 cite URLs | pass | 5 of 5 contain https links |
| no workspace-specific identifiers | pass | grep for catalog, user, warehouse and domain ids in research/ and semantics/: none |

## Requests

* Owner: approve deleting (moving to Trash) `docs/semantics/customer.md`, or delete it manually. Once it is gone, `parse_glossary` will return 23 terms and session 02 is complete.
* Session 05/07 (later waves): use the term names Bakehouse Customer and Bakehouse Supplier for pages and metric view synonyms.

## Files modified

* Created: `docs/semantics/bakehouse_customer.md`, `docs/semantics/bakehouse_supplier.md`
* Edited: `docs/semantics/{approved_supplier,cardholder_data,customer_coverage,franchise,purchase_frequency,repeat_customer_rate,revenue_per_customer,supplier_coverage}.md`, `docs/research/05_domain_subdomain_proposal.md`
* Deleted (Trash): `docs/semantics/supplier.md`
