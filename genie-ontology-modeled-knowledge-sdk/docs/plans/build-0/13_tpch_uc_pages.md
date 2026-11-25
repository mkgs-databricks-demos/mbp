# Session 13: TPC-H Dogfood — UC Pages Registration

## Scope
Register the TPC-H glossary (`examples/tpch/docs/semantics/`) as UC Pages with `genie_ontology_modeled_knowledge_sdk.pages`: a dry run first, then a real upsert. Record the outcome in `examples/tpch/docs/pages/pages_registration.md`. Domain/subdomain creation stays opt-in (L100 decision 2): do not create domains. Associate pages with a domain only if one is already given.

## Context
* [L200-F](../../design/L200-F-registration-pipeline.md) Wave 5.5; session 04 `pages.py`; load the `discover-pages` skill for the endpoints and publish rules.
* Risk: Pages writes may be refused to unattended job tasks. If a write is refused, stop `blocked`, keep the dry-run payloads in the results file, and give the owner the exact command or notebook cell that publishes them. Session 14 runs in parallel and does not depend on this session.
* Page titles and content are generic (TPC-H terms). Page ids and URLs go only in the session summary.

## Tasks
1. `parse_glossary` -> `upsert_pages(dry_run=True)`: review the payloads (one per term).
2. `upsert_pages(dry_run=False)`, then run it again to prove idempotency (0 changes).
3. `pages_registration.md`: a table of term, action (created/updated/unchanged/failed), and reason on failure.

## Acceptance Criteria
- [ ] Every glossary term has a row in `pages_registration.md`.
- [ ] Either all pages are created/unchanged and a second upsert reports 0 changes, or the session status is `blocked` with the refusal message and the owner command.
- [ ] No domains were created.

## Owned Paths / Assets
- `examples/tpch/docs/pages/**`
- Workspace: UC Pages for the TPC-H glossary terms.

## Dependencies
- Session 10a: glossary. Session 04: `pages.py`. Session 12: registered metric views (pages may link to them).
