# Session 31: TPC-H Glossary as Draft UC Pages (Development Domain)

## Scope
Publish the 23 TPC-H glossary terms as **DRAFT** pages in the development Discover domain, record every created page id, and prove idempotency. Never touch pages this build did not create; never create domains.

## Context
* Build-0 session 13 deferred Pages (no domain). Owner decision: the development domain is an existing owner-controlled domain ([summary](../../sessions/2026-11-25_build-1-dev-pages-domain.md)); its id is `pages_domain_id` in `.local/build-1.json` and must never appear in a committed file.
* Rules: drafts only; record ids in `examples/tpch/docs/pages/pages_registration.md` for cleanup; the domain's existing pages are off limits (session 20's `only_ids` + domain scoping enforce it).
* Authorized: `workspace.write` for DRAFT pages of these 23 terms in that domain. If the job task is refused the write, stop `blocked` with the refusal text and the exact owner command (the gate allows that).

## Tasks
1. Dry run with `domain_id`: report creates, updates, collisions (other domains) and not-owned same-title pages in the domain.
2. Live upsert with `status="DRAFT"`, `only_ids` from any ids already in `pages_registration.md`.
3. Rewrite `pages_registration.md` with `pages.format_registration_table` (domain shown as "development domain") plus a cleanup section (one `DELETE /api/2.0/knowledge/pages/{id}` per recorded id, as an owner step).
4. Second upsert: 0 changes.

## Acceptance Criteria
- [ ] Gate check `pages_drafts`.
- [ ] grep of the owned files finds no domain id.

## Owned Paths / Assets
- `examples/tpch/docs/pages/**`; DRAFT pages for the TPC-H terms in the development domain.

## Dependencies
- Sessions 20 (pages), 30.
