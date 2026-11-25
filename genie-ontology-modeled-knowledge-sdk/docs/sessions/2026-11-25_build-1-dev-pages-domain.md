# Build-1 development Pages domain

Date: 2026-11-25 | Branch: `mg-genie-ontology-build-1-dev-domain`

## Problem
The TPC-H glossary was never published to UC Pages in build-0 because no Discover domain existed for it. Creating one is not possible: the metastore has reached its maximum number of domains.

## Root cause
The metastore's domain quota is used up. The SDK needs some domain for development and dogfooding Pages, and that domain must let us remove the SDK's pages later.

## Investigation
* Listed every domain (11 API pages) and filtered by business and technical owner ids: the owner (Matthew Giglia) owns two domains.

| Domain | Id | Owner roles | Other owners | Pages | Clashes with the 23 TPC-H titles |
|---|---|---|---|---|---|
| `mkgs_hc_finance` | `domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3` | business + technical | Aaron Zavora (business) | 18, all `DRAFT` | none |
| `mkgs_underwriting` | `domains/61901539-1958-4b2e-8266-070462db8291` | technical only | Ed Leahy, Aaron Zavora (business) | 30, all `DRAFT` | none |

* `mkgs_underwriting` holds the live Lakeside Health Plan underwriting demo, and other people are its business owners: not used.
* Other people's demo or sandbox domains were not considered: cleaning up later must not touch someone else's domain.

## Decision (owner)
**Build 1 uses `mkgs_hc_finance` (`domains/d3e01d7d-3bd8-4049-80f2-a4f9a1ffc8c3`) for Pages development and the TPC-H dogfood.**

Rules:
* **Drafts only.** Write `DRAFT` pages only; never publish SDK or TPC-H pages in this domain. Its description is "Certified data products for healthcare finance analytics", so TPC-H pages are temporary residents.
* **Record ids for cleanup.** Record every created page id, with its title, in `examples/tpch/docs/pages/pages_registration.md`. Cleanup is one `DELETE /api/2.0/knowledge/pages/{id}` per recorded id. As a fallback, match the 23 TPC-H titles, which do not exist in the domain today.
* **Leave existing pages alone.** Never update or delete the domain's existing 18 healthcare finance pages. Live upserts must pass `domain_id` (build-1 R2 item 2: matching scoped to the domain).
* **Keep the id out of the SDK.** The domain id lives only in session summaries, gitignored files, or `sdk_config.json` `pages_domain_id` for a run project (R3 item 3), never in SDK code or templates.
* **Move off it if needed.** When a dedicated domain becomes available, delete the recorded pages and re-run the upsert against the new domain.

## Changes
* `docs/plans/build-1/REQUESTS.md`: R3 item 3 notes the development domain decision and its rules.
* `PROJECT_MEMORY.md`: new "Build-1 decisions" section; next step 5 points at it.

## Files modified
* `docs/plans/build-1/REQUESTS.md`, `PROJECT_MEMORY.md`, this summary, `docs/sessions/INDEX.md`
