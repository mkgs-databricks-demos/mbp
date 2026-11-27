# UC Pages Results — bakehouse_retail_sales

Wave 4, session 07, build run 38498872047824. Live `upsert_pages(..., domain_id=<sdk_config.json pages_domain_id>, dry_run=False, status="DRAFT", only_ids=[])` with the installed SDK wheel 0.1.1. Domain: `domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3` (from `sdk_config.json`). No domain or subdomain was created; subdomains below come from the term files (Discover has no subdomain object for them).

## Summary

* 23 merged terms (23 from `docs/semantics/`, 0 from `docs/context/glossary_candidates/`, which is absent).
* **21 created** as `DRAFT` in the domain. **2 skipped** (`Customer`, `Supplier`): a TPC-H page with the same title already exists in this shared domain. It was not created by this build, so it was not overwritten. **0 errors.**
* The domain went from 41 to 62 pages (+21). After the run, all 21 created ids are listed in the domain with state `DRAFT`. The two TPC-H pages kept their `update_time` (2026-11-26T03:17:54.171Z and 2026-11-26T03:17:57.406Z).
* Idempotency: a second dry run with `only_ids` = the 21 created ids reported 21 `unchanged` and 2 `skipped`.

## Pages

| term | action | page id | status | domain / subdomain | error / note |
|---|---|---|---|---|---|
| Approved Supplier | created | bf8d3c5f-b0f0-4882-917e-e44200ac2cf9 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Average Transaction Value | created | e632addc-4d3e-44f0-bded-4148684828d8 | DRAFT | bakehouse_retail_sales / sales | none |
| Cardholder Data | created | 424ae16f-ef38-4182-a221-e9222373fc24 | DRAFT | bakehouse_retail_sales / sales | none |
| Comparable Franchise Sales | created | b106fdb6-561a-493f-93a9-e30f3b73751d | DRAFT | bakehouse_retail_sales / sales | none |
| Customer | skipped | - (title held by TPC-H page 832d2cab-3758-440d-8797-ae33e6d75560) | - | bakehouse_retail_sales / customers | not published: exists_not_owned, owner decision needed |
| Customer Coverage | created | 150849da-986f-4173-b94b-a7d26b60c448 | DRAFT | bakehouse_retail_sales / customers | none |
| Franchise | created | 4e7d62d3-253e-4a91-b570-c3af247a0165 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Gross Sales | created | e13d9966-c6d5-46ad-a544-e6d6d1f653ff | DRAFT | bakehouse_retail_sales / sales | none |
| Net Sales | created | 96832c88-5c8d-4788-875c-f4e2d344d31f | DRAFT | bakehouse_retail_sales / sales | none |
| Payment Method | created | 97a8e41e-594d-4772-8410-38996cda5767 | DRAFT | bakehouse_retail_sales / sales | none |
| Payment Method Mix | created | 6e5163c1-dced-4a69-9c78-e71f454c388f | DRAFT | bakehouse_retail_sales / sales | none |
| Product | created | 9e526717-d847-4475-80cf-946facf36d78 | DRAFT | bakehouse_retail_sales / sales | none |
| Product Mix | created | 790c50b4-b600-4fa3-bdaf-00a2fd850cbc | DRAFT | bakehouse_retail_sales / sales | none |
| Purchase Frequency | created | d8737722-c9bf-43cf-899f-2670d2f29284 | DRAFT | bakehouse_retail_sales / customers | none |
| Repeat Customer Rate | created | 787d44b4-939b-474a-9efe-b58452db0e57 | DRAFT | bakehouse_retail_sales / customers | none |
| Revenue per Customer | created | 35e0a5c1-ee4a-4b0e-be87-a2ba08f34167 | DRAFT | bakehouse_retail_sales / customers | none |
| Sales per Franchise | created | 8d85e110-b0cb-4db9-96b9-8ba877270a54 | DRAFT | bakehouse_retail_sales / sales | none |
| Sales Transaction | created | d362953b-d6d9-44f8-a100-f2af91e7ea34 | DRAFT | bakehouse_retail_sales / sales | none |
| Supplier | skipped | - (title held by TPC-H page 2f18a2a0-ba44-45bc-8ae0-d894bc40f226) | - | bakehouse_retail_sales / franchise_supply | not published: exists_not_owned, owner decision needed |
| Supplier Coverage | created | 475619f2-92a3-4a2f-8ff2-ecee6f3682d8 | DRAFT | bakehouse_retail_sales / franchise_supply | none |
| Unit Price | created | 9d54f330-d008-4d3f-9201-8d0b783e10d0 | DRAFT | bakehouse_retail_sales / sales | none |
| Units per Transaction | created | c7d4a1e7-6920-4f33-9e53-14907698f7a4 | DRAFT | bakehouse_retail_sales / sales | none |
| Units Sold | created | ed6e8132-5fdc-4507-9dc8-cd4720a37a84 | DRAFT | bakehouse_retail_sales / sales | none |

## Created page ids (for tuning)

Use these 21 ids as `only_ids` on re-runs:

bf8d3c5f-b0f0-4882-917e-e44200ac2cf9, e632addc-4d3e-44f0-bded-4148684828d8, 424ae16f-ef38-4182-a221-e9222373fc24, b106fdb6-561a-493f-93a9-e30f3b73751d, 150849da-986f-4173-b94b-a7d26b60c448, 4e7d62d3-253e-4a91-b570-c3af247a0165, e13d9966-c6d5-46ad-a544-e6d6d1f653ff, 96832c88-5c8d-4788-875c-f4e2d344d31f, 97a8e41e-594d-4772-8410-38996cda5767, 6e5163c1-dced-4a69-9c78-e71f454c388f, 9e526717-d847-4475-80cf-946facf36d78, 790c50b4-b600-4fa3-bdaf-00a2fd850cbc, d8737722-c9bf-43cf-899f-2670d2f29284, 787d44b4-939b-474a-9efe-b58452db0e57, 35e0a5c1-ee4a-4b0e-be87-a2ba08f34167, 8d85e110-b0cb-4db9-96b9-8ba877270a54, d362953b-d6d9-44f8-a100-f2af91e7ea34, 475619f2-92a3-4a2f-8ff2-ecee6f3682d8, 9d54f330-d008-4d3f-9201-8d0b783e10d0, c7d4a1e7-6920-4f33-9e53-14907698f7a4, ed6e8132-5fdc-4507-9dc8-cd4720a37a84

## Owner decision needed (Customer, Supplier)

Page titles are matched case-insensitively within a domain. In this shared domain, `Customer` and `Supplier` already belong to the TPC-H glossary. Options:

1. Point `sdk_config.json` `pages_domain_id` at a domain used only by bakehouse, then re-run session 07. The 21 pages above would need to be moved, or recreated there and deleted here.
2. Approve title-qualified page names for these two terms (for example `Bakehouse Customer`, `Bakehouse Supplier`). Session 02 owns the term files.
3. Approve overwriting the two TPC-H pages. Not recommended: it breaks the TPC-H glossary.
