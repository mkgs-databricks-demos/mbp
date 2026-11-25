# Session 10a: TPC-H Dogfood — Domain Research & Glossary

## Scope
Dogfood the `ontology-domain-research` skill on the TPC-H supply-chain domain. Write research docs, glossary candidates and the domain/subdomain proposal under `examples/tpch/docs/research/` and `examples/tpch/docs/semantics/`. Record skill gaps for build 1.

## Context
* Load `skills/ontology-domain-research/SKILL.md` (session 05a) and follow it exactly. The point is to test the skill, so do not improvise beyond it. If it is unclear, note the gap in the summary and do the reasonable thing.
* Domain context from `examples/tpch/sdk_config.json`: TPC-H models a wholesale supplier: customers place orders of line items for parts supplied by suppliers, across nations and regions.
* KPIs to look for (seed list, verify with sources): revenue (`l_extendedprice * (1 - l_discount)`), discount revenue, order volume, average order value, on-time shipping (`l_shipdate` vs `l_commitdate`), return rate (`l_returnflag`), supplier cost (`ps_supplycost`), and market-share-by-nation style TPC-H query metrics.
* Glossary file contract: see [INDEX.md](../INDEX.md#cross-session-contracts) (front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources`).
* No supplemental context exists for TPC-H. Session 10b runs the EDA in parallel; do not read or write `docs/data_profiles/`.

## Tasks
1. At least 3 research docs (terminology, KPIs, industry/benchmark context: the TPC-H spec itself is a valid source), each with cited URLs.
2. 15-30 glossary candidates in `examples/tpch/docs/semantics/` (one file per term).
3. `examples/tpch/docs/research/05_domain_subdomain_proposal.md`: domain `tpch_supply_chain` with subdomains (e.g. sales, fulfillment, procurement).
4. A "Skill gaps" section in the session summary.

## Acceptance Criteria
- [ ] `examples/tpch/docs/research/` has at least 3 docs plus the proposal; every doc has at least 1 URL citation.
- [ ] `examples/tpch/docs/semantics/` has at least 15 term files, and `pages.parse_glossary` (session 04) parses all of them without error.
- [ ] Only owned paths changed.

## Owned Paths / Assets
- `examples/tpch/docs/research/**`
- `examples/tpch/docs/semantics/**`

## Dependencies
- Session 05a: research skill. Session 09: `examples/tpch/` scaffold. Session 04: `parse_glossary`.
