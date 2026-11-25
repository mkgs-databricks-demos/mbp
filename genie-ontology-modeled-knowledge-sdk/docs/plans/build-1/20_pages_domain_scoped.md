# Session 20: Pages — Domain-Scoped Upserts, Drafts, Bulk Terms (R4.2)

## Scope
Make `pages.upsert_pages` safe in a shared account: live writes require a domain and only touch that domain's pages; drafts by default; report created ids; link-safe descriptions; a bulk term writer. Mocked tests only, no live API writes.

## Context
* [REQUESTS R4](REQUESTS.md#r4-fix-the-library-and-template-defects) item 2; review gap G6.
* Build-0 observations 21 (account-wide title matching collides with other teams' pages; 8 collisions found), 22 (descriptions truncated mid-link; the close-out fixed abbreviations only), 8 (one file per term costs two tool calls).
* Build 1 develops Pages in an existing owner-controlled domain: drafts only, record every created id, never touch existing pages ([dev Pages domain summary](../../sessions/2026-11-25_build-1-dev-pages-domain.md)). The SDK must make those rules the default behavior, not a convention.

## Tasks
1. `upsert_pages(terms, client, *, domain_id=None, dry_run=True, status="DRAFT", only_ids=None)`:
   * live run (`dry_run=False`) without `domain_id`: every term is an `error` result, nothing written;
   * matching by title only among pages in `domain_id`; a same-title page in another domain is reported `collision_other_domain` and never updated;
   * `only_ids` (ids created earlier, e.g. read from `pages_registration.md`): updates are allowed only for pages in this set; any other same-title page in the domain is reported `exists_not_owned` and skipped;
   * result per term: `action` (`created`, `updated`, `unchanged`, `skipped`, `error`), `page_id`, `status`, `reason`.
2. Dry runs may list account-wide to report collisions; live runs never list outside the domain.
3. `_first_sentence` / description builder: strip markdown links (keep link text) before truncating at 160 characters.
4. `write_terms(terms, folder)`: writes many glossary term files in one call (front matter + sections), idempotent, returns paths (obs 8).
5. `format_registration_table(results)`: markdown rows `term | page id | status | action`, with the domain shown only as "development domain" (no id).

## Acceptance Criteria
- [ ] Gate check `r4_tests` (the pages part): fake client proves the other-domain page is never updated, a live upsert without `domain_id` writes nothing, a not-owned same-title page in the domain is skipped.
- [ ] Description test with a link at character 150.
- [ ] `write_terms` round-trips through `parse_glossary`.

## Owned Paths
- `src/genie_ontology_modeled_knowledge_sdk/pages.py`, `tests/test_pages.py`, `tests/fixtures/glossary/**`

## Dependencies
- Session 18.
