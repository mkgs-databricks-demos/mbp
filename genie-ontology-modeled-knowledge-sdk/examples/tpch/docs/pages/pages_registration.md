# TPC-H Glossary -> UC Pages Registration

Source: `examples/tpch/docs/semantics/` (23 term files, parsed with `genie_ontology_modeled_knowledge_sdk.pages.parse_glossary`, 0 parse errors).
Build-1 session 31 (wave 1-6, runs `1020175336236697` and `629243800379582`), 2026-11-26. Domain id: `pages_domain_id` in the gitignored `.local/build-1.json` (never written here).

## Outcome

**23 DRAFT pages created in the development domain; a second upsert reports 0 changes (23 `unchanged`).**

| Pass | Call | Result |
| --- | --- | --- |
| 1. Dry run | `upsert_pages(terms, client, domain_id=..., dry_run=True)` | 23 `created` (dry run); 0 same-title pages in the domain (no `exists_not_owned`); 7 titles also exist in other domains (`collision_other_domain`: Average Order Value 3, Customer 12, Market Segment 3, Part 4, Return Rate 3, Revenue 9, Supplier 5). Those pages were never fetched for update or written. |
| 2. Live upsert | `dry_run=False, status="DRAFT", only_ids=[]` (no ids recorded before) | 23 `created`, 23 distinct page ids, all `DRAFT` and in the development domain (checked with `GET` per page). The domain went from 18 to 41 pages; the 18 existing pages are byte-identical before and after (sha256 of the full `GET` response). |
| 3. Second upsert (run `1020175336236697`) | `dry_run=False, only_ids=<the 23 ids>` | 11 `unchanged`, 12 `updated` (field `synonyms` only): the API stores synonyms sorted and `pages._normalize` compared them in order. |
| 4. Rerun after the SDK fix (run `629243800379582`, commit `ea5d5eb`: synonyms compared order-insensitively) | dry run, then two live upserts, all with `only_ids=<the 23 ids>` | dry run 23 `unchanged`; live upsert 23 `unchanged`; second live upsert 23 `unchanged` (**0 changes**). All 23 pages `DRAFT` in the development domain (`GET` per page); the domain still has 41 pages, all byte-identical before and after (sha256 of the full `GET` response). |

## Created pages

Domain: development domain

| Term | Page id | Status | Action |
| --- | --- | --- | --- |
| Average Order Value | 4704446d-5599-4bde-aa6a-b791a394c09e | DRAFT | created |
| Customer | 832d2cab-3758-440d-8797-ae33e6d75560 | DRAFT | created |
| Discount Revenue | ac5229bb-fa6b-4d97-a513-d049727417d3 | DRAFT | created |
| Extended Price | 28489dc6-f42a-4585-81e6-c996331065fb | DRAFT | created |
| Gross Charge | e8ec8341-0bf1-4001-9849-34fa3a431a2f | DRAFT | created |
| Inventory Value | e8f71590-a669-43a1-ab2b-b485f625e3da | DRAFT | created |
| Late Receipt | b7d426de-6231-4765-9ef2-09f2a54554db | DRAFT | created |
| Line Item | 6b033449-b70c-42f4-adc0-d12990958013 | DRAFT | created |
| Market Segment | 793b314d-9826-460d-9fbd-a3fecdd35730 | DRAFT | created |
| National Market Share | 05defcc6-0fa3-433b-9661-aeac09ef2dd7 | DRAFT | created |
| On-Time Shipping Rate | fa27b296-b864-463e-9672-a232bb72869b | DRAFT | created |
| Order Fulfillment Cycle Time | 74daf7c3-a0c5-43be-9f2e-ed0357c1c833 | DRAFT | created |
| Order Priority | 69fbcdc0-c161-4c94-a3eb-c208335096cc | DRAFT | created |
| Order Volume | 86644282-884f-47b8-99f9-8b55f38441d0 | DRAFT | created |
| Part | bb75472f-b01b-4c8a-ba78-eb4049c6d007 | DRAFT | created |
| Perfect Order Rate | 6dfe3003-c9e6-49d1-8f5a-fbdbbd852837 | DRAFT | created |
| Profit | 38887f55-5b70-4266-bbcc-1904052b6c73 | DRAFT | created |
| Return Flag | 6152385d-df60-4ca6-90c7-9244f170c389 | DRAFT | created |
| Return Rate | b25a694d-21dc-4ec7-9c91-acdfcea5a278 | DRAFT | created |
| Revenue | 0bfa12d9-22f0-42db-bb98-3316271f2d4a | DRAFT | created |
| Ship Mode | d49517ba-7784-4667-962e-7a6ede3d5534 | DRAFT | created |
| Supplier | 2f18a2a0-ba44-45bc-8ae0-d894bc40f226 | DRAFT | created |
| Supply Cost | bb6b82c9-4cef-4eb8-8707-d89ec3c9f6ed | DRAFT | created |

Page bodies are not copied here: `to_page_payload(term)` renders them deterministically from each term file. Later runs must pass these 23 ids as `only_ids` (and the same `domain_id`), so no other page in the domain is ever updated.

## Cleanup (owner step)

These pages are temporary residents of the development domain. To remove them, delete exactly the recorded ids, one call per page (never by title alone):

```
DELETE /api/2.0/knowledge/pages/4704446d-5599-4bde-aa6a-b791a394c09e  # Average Order Value
DELETE /api/2.0/knowledge/pages/832d2cab-3758-440d-8797-ae33e6d75560  # Customer
DELETE /api/2.0/knowledge/pages/ac5229bb-fa6b-4d97-a513-d049727417d3  # Discount Revenue
DELETE /api/2.0/knowledge/pages/28489dc6-f42a-4585-81e6-c996331065fb  # Extended Price
DELETE /api/2.0/knowledge/pages/e8ec8341-0bf1-4001-9849-34fa3a431a2f  # Gross Charge
DELETE /api/2.0/knowledge/pages/e8f71590-a669-43a1-ab2b-b485f625e3da  # Inventory Value
DELETE /api/2.0/knowledge/pages/b7d426de-6231-4765-9ef2-09f2a54554db  # Late Receipt
DELETE /api/2.0/knowledge/pages/6b033449-b70c-42f4-adc0-d12990958013  # Line Item
DELETE /api/2.0/knowledge/pages/793b314d-9826-460d-9fbd-a3fecdd35730  # Market Segment
DELETE /api/2.0/knowledge/pages/05defcc6-0fa3-433b-9661-aeac09ef2dd7  # National Market Share
DELETE /api/2.0/knowledge/pages/fa27b296-b864-463e-9672-a232bb72869b  # On-Time Shipping Rate
DELETE /api/2.0/knowledge/pages/74daf7c3-a0c5-43be-9f2e-ed0357c1c833  # Order Fulfillment Cycle Time
DELETE /api/2.0/knowledge/pages/69fbcdc0-c161-4c94-a3eb-c208335096cc  # Order Priority
DELETE /api/2.0/knowledge/pages/86644282-884f-47b8-99f9-8b55f38441d0  # Order Volume
DELETE /api/2.0/knowledge/pages/bb75472f-b01b-4c8a-ba78-eb4049c6d007  # Part
DELETE /api/2.0/knowledge/pages/6dfe3003-c9e6-49d1-8f5a-fbdbbd852837  # Perfect Order Rate
DELETE /api/2.0/knowledge/pages/38887f55-5b70-4266-bbcc-1904052b6c73  # Profit
DELETE /api/2.0/knowledge/pages/6152385d-df60-4ca6-90c7-9244f170c389  # Return Flag
DELETE /api/2.0/knowledge/pages/b25a694d-21dc-4ec7-9c91-acdfcea5a278  # Return Rate
DELETE /api/2.0/knowledge/pages/0bfa12d9-22f0-42db-bb98-3316271f2d4a  # Revenue
DELETE /api/2.0/knowledge/pages/d49517ba-7784-4667-962e-7a6ede3d5534  # Ship Mode
DELETE /api/2.0/knowledge/pages/2f18a2a0-ba44-45bc-8ae0-d894bc40f226  # Supplier
DELETE /api/2.0/knowledge/pages/bb6b82c9-4cef-4eb8-8707-d89ec3c9f6ed  # Supply Cost
```
