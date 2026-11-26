# Session 07: UC Pages Registration

## Scope
Publish the `bakehouse_retail_sales` glossary as UC Pages. Parse the terms, run a dry-run upsert, then do the live upsert. Associate pages with the domain/subdomain when one exists, and record the results in `docs/pages/`. This session runs in parallel with session 08 and does not deploy.

## Context
* Skill: the platform `discover-pages` skill covers the Pages API. The SDK wraps it.
* SDK functions (`genie_ontology_modeled_knowledge_sdk.pages`): `parse_glossary(dir)`, `to_page_payload(term, domain_id=None)`, `upsert_pages(terms, client, dry_run=True)`, `PagesClient`, `RestPagesClient(ws)`.
* Inputs: `docs/semantics/` (session 02) and `docs/context/glossary_candidates/` (session 03, may be absent). When both define a term, the `docs/semantics/` version wins and the context candidate's synonyms and sources are merged in. `docs/research/05_domain_subdomain_proposal.md` gives the domain structure. `docs/registration/registration_results.md` lists the registered metric views to link from Data usage.
* Prerequisite (wave `manual_prereqs`): `sdk_config.json` `pages_domain_id`, an existing Discover domain the owner controls. Without it, run the dry run only and end `pass` with "publishing deferred" in `pages_results.md`.
* Live upserts always pass `domain_id` = `pages_domain_id` and `status=DRAFT`, unless `sdk_config.json` `pages_status` says otherwise.
* Approvals: creating and updating pages in that domain is approved in the session's `authorizations`. Creating domains is opt-in (design decision 2). Propose them in `docs/pages/domain_proposal.md`, but do not create a domain unless the prompt approves it.

## Tasks
1. Parse both glossary folders and merge the terms.
2. Run `upsert_pages(terms, RestPagesClient(ws), dry_run=True)` and write the planned creates and updates to `docs/pages/pages_dry_run.md`.
3. Only when `pages_domain_id` is set: run the live upsert with that `domain_id` and the configured status (default `DRAFT`). Otherwise skip to task 4 and record "publishing deferred".
4. Write `docs/pages/pages_results.md` with one row per term: term, action (created, updated or unchanged), page id, domain/subdomain, error.

## Acceptance Criteria
- [ ] `pages_results.md` has one row per merged term with page id and status, and no row has an error; or it says "publishing deferred" after a clean dry run.
- [ ] No domain was created without an approval.
- [ ] Page ids are recorded for the tuning stage.

## Owned Paths
- `docs/pages/**`

## Dependencies
- Sessions 02 and 03: glossary files. Session 06: registered metric views.
