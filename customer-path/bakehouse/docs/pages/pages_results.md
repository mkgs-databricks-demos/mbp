# UC Pages Results — bakehouse_retail_sales

Wave 4, session 07, build run 409860738864401. Live `upsert_pages(..., domain_id=<sdk_config.json pages_domain_id>, dry_run=False, status="DRAFT", only_ids=<the 23 ids below>)` with the installed SDK wheel 0.1.1. Domain: `domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3` (from `sdk_config.json`). No domain or subdomain was created; subdomains below come from the term files (Discover has no subdomain object for them).

## Summary

* 23 merged terms (23 from `docs/semantics/`, 0 from `docs/context/glossary_candidates/`, which is absent). `Customer` and `Supplier` are now `Bakehouse Customer` and `Bakehouse Supplier` (session 02 rename).
* This run: **0 created**, **0 updated**, **23 unchanged**, **0 skipped**, **0 errors** (dry run and live run agree). One bakehouse page per term: 23 pages.
* The domain holds 64 pages before and after the run. All 23 bakehouse ids are listed in the domain with state `DRAFT`, the domain field equals `pages_domain_id`, and their titles equal the 23 term names, each once. The TPC-H `Customer` and `Supplier` pages kept their `update_time` (2026-11-26T03:17:54.171Z and 2026-11-26T03:17:57.406Z); the latest bakehouse page `update_time` is still 2026-11-27T13:55:48.788Z, so nothing was rewritten.
* History: build run 38498872047824 created 21 pages; build run 244030216249267 created `Bakehouse Customer` and `Bakehouse Supplier` and updated 8 bodies after the rename.

## Pages

`action` is this run's action (build run 409860738864401).

| term | action | page id | status | domain / subdomain | error / note |
|---|---|---|---|---|---|
| Approved Supplier | unchanged | bf8d3c5f-b0f0-4882-917e-e44200ac2cf9 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Average Transaction Value | unchanged | e632addc-4d3e-44f0-bded-4148684828d8 | DRAFT | bakehouse_retail_sales / sales | none |
| Bakehouse Customer | unchanged | 7766e30f-e105-4f14-a76a-2ed38ec0d1e0 | DRAFT | bakehouse_retail_sales / customers | none |
| Bakehouse Supplier | unchanged | 7618e9c2-7033-4468-8520-a6be13eef8cc | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Cardholder Data | unchanged | 424ae16f-ef38-4182-a221-e9222373fc24 | DRAFT | bakehouse_retail_sales / sales | none |
| Comparable Franchise Sales | unchanged | b106fdb6-561a-493f-93a9-e30f3b73751d | DRAFT | bakehouse_retail_sales / sales | none |
| Customer Coverage | unchanged | 150849da-986f-4173-b94b-a7d26b60c448 | DRAFT | bakehouse_retail_sales / customers | none |
| Franchise | unchanged | 4e7d62d3-253e-4a91-b570-c3af247a0165 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Gross Sales | unchanged | e13d9966-c6d5-46ad-a544-e6d6d1f653ff | DRAFT | bakehouse_retail_sales / sales | none |
| Net Sales | unchanged | 96832c88-5c8d-4788-875c-f4e2d344d31f | DRAFT | bakehouse_retail_sales / sales | none |
| Payment Method | unchanged | 97a8e41e-594d-4772-8410-38996cda5767 | DRAFT | bakehouse_retail_sales / sales | none |
| Payment Method Mix | unchanged | 6e5163c1-dced-4a69-9c78-e71f454c388f | DRAFT | bakehouse_retail_sales / sales | none |
| Product | unchanged | 9e526717-d847-4475-80cf-946facf36d78 | DRAFT | bakehouse_retail_sales / sales | none |
| Product Mix | unchanged | 790c50b4-b600-4fa3-bdaf-00a2fd850cbc | DRAFT | bakehouse_retail_sales / sales | none |
| Purchase Frequency | unchanged | d8737722-c9bf-43cf-899f-2670d2f29284 | DRAFT | bakehouse_retail_sales / customers | none |
| Repeat Customer Rate | unchanged | 787d44b4-939b-474a-9efe-b58452db0e57 | DRAFT | bakehouse_retail_sales / customers | none |
| Revenue per Customer | unchanged | 35e0a5c1-ee4a-4b0e-be87-a2ba08f34167 | DRAFT | bakehouse_retail_sales / customers | none |
| Sales per Franchise | unchanged | 8d85e110-b0cb-4db9-96b9-8ba877270a54 | DRAFT | bakehouse_retail_sales / sales | none |
| Sales Transaction | unchanged | d362953b-d6d9-44f8-a100-f2af91e7ea34 | DRAFT | bakehouse_retail_sales / sales | none |
| Supplier Coverage | unchanged | 475619f2-92a3-4a2f-8ff2-ecee6f3682d8 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Unit Price | unchanged | 9d54f330-d008-4d3f-9201-8d0b783e10d0 | DRAFT | bakehouse_retail_sales / sales | none |
| Units per Transaction | unchanged | c7d4a1e7-6920-4f33-9e53-14907698f7a4 | DRAFT | bakehouse_retail_sales / sales | none |
| Units Sold | unchanged | ed6e8132-5fdc-4507-9dc8-cd4720a37a84 | DRAFT | bakehouse_retail_sales / sales | none |

## Created page ids (for tuning)

Use these 23 ids as `only_ids` on re-runs:

bf8d3c5f-b0f0-4882-917e-e44200ac2cf9, e632addc-4d3e-44f0-bded-4148684828d8, 424ae16f-ef38-4182-a221-e9222373fc24, b106fdb6-561a-493f-93a9-e30f3b73751d, 150849da-986f-4173-b94b-a7d26b60c448, 4e7d62d3-253e-4a91-b570-c3af247a0165, e13d9966-c6d5-46ad-a544-e6d6d1f653ff, 96832c88-5c8d-4788-875c-f4e2d344d31f, 97a8e41e-594d-4772-8410-38996cda5767, 6e5163c1-dced-4a69-9c78-e71f454c388f, 9e526717-d847-4475-80cf-946facf36d78, 790c50b4-b600-4fa3-bdaf-00a2fd850cbc, d8737722-c9bf-43cf-899f-2670d2f29284, 787d44b4-939b-474a-9efe-b58452db0e57, 35e0a5c1-ee4a-4b0e-be87-a2ba08f34167, 8d85e110-b0cb-4db9-96b9-8ba877270a54, d362953b-d6d9-44f8-a100-f2af91e7ea34, 475619f2-92a3-4a2f-8ff2-ecee6f3682d8, 9d54f330-d008-4d3f-9201-8d0b783e10d0, c7d4a1e7-6920-4f33-9e53-14907698f7a4, ed6e8132-5fdc-4507-9dc8-cd4720a37a84, 7766e30f-e105-4f14-a76a-2ed38ec0d1e0, 7618e9c2-7033-4468-8520-a6be13eef8cc

## Resolved: Customer / Supplier collision

The owner chose title-qualified names (option 2 of the earlier run): `sdk_config.json` `domain_context` renames the terms to `Bakehouse Customer` and `Bakehouse Supplier`, and session 02 applied it. Both now have their own bakehouse pages. The TPC-H `Customer` and `Supplier` pages were not touched.
