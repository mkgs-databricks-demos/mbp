# UC Pages Dry Run — bakehouse_retail_sales

## Build run 244030216249267 (current)

`upsert_pages(terms, RestPagesClient(ws), domain_id=<sdk_config.json pages_domain_id>, dry_run=True, only_ids=<21 ids from build run 38498872047824>)`, installed SDK wheel 0.1.1. Inputs: `docs/semantics/` 23 terms, all parsed (now `Bakehouse Customer` and `Bakehouse Supplier`, no bare `Customer` / `Supplier`); `docs/context/glossary_candidates/` absent. Domain held 62 pages before the run.

Planned: **2 creates, 8 updates, 13 unchanged, 0 skipped, 0 errors.**

| term | planned action | page id | changed fields | collisions (other domains, advisory) |
|---|---|---|---|---|
| Bakehouse Customer | created | - | display_name, description, synonyms, body | 0 |
| Bakehouse Supplier | created | - | display_name, description, synonyms, body | 0 |
| Approved Supplier | updated | bf8d3c5f-b0f0-4882-917e-e44200ac2cf9 | body | 0 |
| Cardholder Data | updated | 424ae16f-ef38-4182-a221-e9222373fc24 | body | 0 |
| Customer Coverage | updated | 150849da-986f-4173-b94b-a7d26b60c448 | body | 0 |
| Franchise | updated | 4e7d62d3-253e-4a91-b570-c3af247a0165 | body | 1 |
| Purchase Frequency | updated | d8737722-c9bf-43cf-899f-2670d2f29284 | body | 0 |
| Repeat Customer Rate | updated | 787d44b4-939b-474a-9efe-b58452db0e57 | body | 0 |
| Revenue per Customer | updated | 35e0a5c1-ee4a-4b0e-be87-a2ba08f34167 | body | 1 |
| Supplier Coverage | updated | 475619f2-92a3-4a2f-8ff2-ecee6f3682d8 | body | 0 |

The other 13 terms are `unchanged`. The updates are the `related_terms` rename (Customer -> Bakehouse Customer, Supplier -> Bakehouse Supplier) in the page body.

## Build run 38498872047824 (earlier)

Wave 4, session 07, build run 38498872047824. `genie_ontology_modeled_knowledge_sdk.pages.upsert_pages(terms, RestPagesClient(ws), domain_id=<sdk_config.json pages_domain_id>, dry_run=True)` with the installed SDK wheel 0.1.1.

## Inputs

* `docs/semantics/`: 23 term files, all 23 parsed by `parse_glossary`.
* `docs/context/glossary_candidates/`: absent (session 03 took the no-inputs path), so nothing was merged.
* Target domain: `sdk_config.json` `pages_domain_id`. Status for new pages: `DRAFT` (`pages_status` not set).

## Planned actions (before the live run)

Planned: 21 creates and 2 updates. `collisions` is the number of pages with the same title in **other** domains (advisory only; those pages are never touched).

| term | planned action | existing page id (in domain) | fields | reason | collisions |
|---|---|---|---|---|---|
| Approved Supplier | created | - | display_name, description, synonyms, body | - | 0 |
| Average Transaction Value | created | - | display_name, description, synonyms, body | - | 0 |
| Cardholder Data | created | - | display_name, description, synonyms, body | - | 0 |
| Comparable Franchise Sales | created | - | display_name, description, synonyms, body | - | 0 |
| Customer | updated | 832d2cab-3758-440d-8797-ae33e6d75560 | description, synonyms, body | collision_other_domain | 12 |
| Customer Coverage | created | - | display_name, description, synonyms, body | - | 0 |
| Franchise | created | - | display_name, description, synonyms, body | collision_other_domain | 1 |
| Gross Sales | created | - | display_name, description, synonyms, body | collision_other_domain | 1 |
| Net Sales | created | - | display_name, description, synonyms, body | collision_other_domain | 3 |
| Payment Method | created | - | display_name, description, synonyms, body | collision_other_domain | 2 |
| Payment Method Mix | created | - | display_name, description, synonyms, body | collision_other_domain | 1 |
| Product | created | - | display_name, description, synonyms, body | collision_other_domain | 4 |
| Product Mix | created | - | display_name, description, synonyms, body | - | 0 |
| Purchase Frequency | created | - | display_name, description, synonyms, body | - | 0 |
| Repeat Customer Rate | created | - | display_name, description, synonyms, body | - | 0 |
| Revenue per Customer | created | - | display_name, description, synonyms, body | collision_other_domain | 1 |
| Sales per Franchise | created | - | display_name, description, synonyms, body | - | 0 |
| Sales Transaction | created | - | display_name, description, synonyms, body | - | 0 |
| Supplier | updated | 2f18a2a0-ba44-45bc-8ae0-d894bc40f226 | description, synonyms, body | collision_other_domain | 5 |
| Supplier Coverage | created | - | display_name, description, synonyms, body | - | 0 |
| Unit Price | created | - | display_name, description, synonyms, body | - | 0 |
| Units per Transaction | created | - | display_name, description, synonyms, body | - | 0 |
| Units Sold | created | - | display_name, description, synonyms, body | - | 0 |

## Finding: the domain is shared

The target domain held 41 pages before this run, from other projects (healthcare payer terms and TPC-H terms). The two planned **updates** (`Customer`, `Supplier`) matched TPC-H pages (their bodies describe `samples.tpch.customer` and `samples.tpch.supplier`). This session did not create them, and the approval covers only the bakehouse glossary pages, so the live run used `only_ids=[]`. That setting makes any existing same-title page `skipped` (`exists_not_owned`) instead of overwritten. See `pages_results.md`.
