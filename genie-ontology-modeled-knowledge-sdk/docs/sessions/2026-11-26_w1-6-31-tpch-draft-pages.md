# 2026-11-26 - Wave 1-6, session 31: TPC-H glossary as DRAFT UC Pages (development domain)

Runs `1020175336236697` (first) and `629243800379582` (rerun after the SDK fix), branch `mg-genie-ontology-build-1-plan` (checked read-only), mode `edit` with `allow_execute`. Authorization used: `workspace.write` for DRAFT pages of the 23 TPC-H terms in the development domain. The domain id was read from `.local/build-1.json` at runtime and is not written in any file this session produced.

## Outcome: pass (after rerun in run `629243800379582`)

23 DRAFT pages exist and are recorded. Run `1020175336236697` stopped blocked: the second upsert reported 12 changes because of an SDK comparison defect in `pages.py`. The owner fixed it in commit `ea5d5eb` (synonyms compared order-insensitively); the rerun reports 0 changes.

## Rerun (run `629243800379582`)

* Branch checked read-only: `mg-genie-ontology-build-1-plan` at `ea5d5eb`, `_normalize` now returns `sorted(value or [])` for `synonyms`.
* Dry run with `only_ids` = the 23 recorded ids: 23 `unchanged` (7 advisory `collision_other_domain`, never written).
* Live upsert (task 2) and second live upsert (task 4), both `only_ids` = the 23 ids: 23 `unchanged` each, **0 changes**, no pages created.
* `GET` per page: 23 `DRAFT`, all in the development domain. Domain page count 41 before and after; all 41 pages byte-identical (sha256 of full `GET`).
* `pages_registration.md`: outcome section updated with pass 4; the created-pages table and cleanup section are unchanged (23 rows, ids equal to the recorded ids). No domain id in the file.

## What was done

1. **Dry run** (`upsert_pages(..., domain_id, dry_run=True)`): 23 `created`, 0 same-title pages in the domain (no `exists_not_owned`), 7 titles collide with pages in other domains (Average Order Value 3, Customer 12, Market Segment 3, Part 4, Return Rate 3, Revenue 9, Supplier 5). Those pages were never written. The domain had 18 pages, all DRAFT.
2. **Live upsert** (`dry_run=False, status="DRAFT", only_ids=[]`): 23 `created`, 23 distinct ids. Independent `GET` per page: right title, development domain, state DRAFT. The domain now has 41 pages. The 18 pre-existing pages are byte-identical (sha256 of the full `GET` response before and after).
3. **Registration**: `examples/tpch/docs/pages/pages_registration.md` rewritten: pass results, `format_registration_table` output (domain shown as "development domain"), and a cleanup section with one `DELETE /api/2.0/knowledge/pages/{id}` per recorded id as an owner step.
4. **Second upsert** (`only_ids` = the 23 ids): 11 `unchanged`, 12 `updated` (only `synonyms`). A further dry run shows the same 12, so the diff repeats on every run.

## Root cause of the idempotency failure

The knowledge-page API returns `synonyms` sorted (case-sensitive), for example `Customer` is sent as `[buyer, account, c_custkey]` and stored as `[account, buyer, c_custkey]`. `pages._normalize("synonyms", v)` returns `list(v)`, so `_diff` compares the lists in order and flags every term whose synonyms are not already sorted (12 of 23). The rewrite has no effect, but the run never reports 0 changes.

Fix (not applied; `src/genie_ontology_modeled_knowledge_sdk/pages.py` and `tests/test_pages.py` are outside this session's `owned_paths`): compare synonyms order-insensitively, e.g. `return sorted(value or [])` for `synonyms` in `_normalize`, plus a mocked test where the fake client stores sorted synonyms and a second upsert reports all `unchanged`. I did not sort the synonyms in the call to make the check pass: that would hide the defect from every other SDK user (guardrail 13).

## Owner command after the fix (rerun of task 4 only)

Run this session again (it is idempotent: with `only_ids` = the recorded 23 ids it creates nothing new), or in a notebook: `pages.upsert_pages(pages.parse_glossary(<ROOT>/examples/tpch/docs/semantics), pages.RestPagesClient(WorkspaceClient()), domain_id=<pages_domain_id from .local/build-1.json>, dry_run=False, only_ids=<23 ids from pages_registration.md>)`. Expected: 23 `unchanged`.

## Checks

| Check | Result |
| --- | --- |
| dry run with domain_id | pass: 23 creates, 0 not-owned, 7 collisions (other domains, untouched) |
| live upsert | pass: 23 created, all DRAFT in the development domain, 18 existing pages unchanged |
| pages_drafts: registration has one row per term with page id and DRAFT, domain shown as "development domain" | pass: 23 rows, ids equal to the created ids |
| pages_drafts: second upsert 0 changes | first run fail (12 `updated`, SDK defect); rerun pass: 23 `unchanged` |
| grep of owned files for the domain id | pass: not found (no `domains/` string either) |

## Files and assets

* Modified: `examples/tpch/docs/pages/pages_registration.md`
* Created: 23 DRAFT knowledge pages in the development domain (ids in `pages_registration.md`)

## Requests

* Resolved: the synonyms fix (owner commit `ea5d5eb`) closed the earlier high-priority request.
* Tuning sessions that reuse these pages (36-41): pass the 23 ids from `pages_registration.md` as `only_ids`, with the same `domain_id`.
