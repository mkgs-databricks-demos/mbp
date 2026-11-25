# Session 10b: TPC-H Dogfood — Deep EDA

## Scope
Dogfood the `ontology-deep-eda` skill on the 8 `samples.tpch` tables. Write one profile per table plus `data_model_summary.md`, with verified join cardinalities, under `examples/tpch/docs/data_profiles/`. Record skill gaps.

## Context
* Load `skills/ontology-deep-eda/SKILL.md` (session 05a) and follow it.
* Tables: `customer`, `orders`, `lineitem`, `part`, `partsupp`, `supplier`, `nation`, `region`. Use read-only SQL on serverless or the overrides' warehouse. Sizes are large (`orders` about 7.5M rows, `lineitem` about 30M rows), so apply the skill's sampling rule for distributions; compute keys and cardinality exactly where the skill requires it.
* Expected relationships to verify (not assume):
  * `lineitem.l_orderkey -> orders.o_orderkey` (many-to-one)
  * `orders.o_custkey -> customer.c_custkey`
  * `lineitem.(l_partkey,l_suppkey) -> partsupp.(ps_partkey,ps_suppkey)`
  * `partsupp -> part`, `partsupp -> supplier`
  * `customer/supplier.nationkey -> nation`, `nation.n_regionkey -> region`
* System tables (lineage/usage) may be denied or empty for `samples`. Use the skill's fallback and record it.
* Do not touch `docs/research/` or `docs/semantics/` (session 10a, same wave).

## Tasks
1. 8 table profiles (structure, nulls, grain/primary key, distinct counts, freshness, volume, materialization signals).
2. `data_model_summary.md`: fact vs dimension tables, a join table (`left`, `right`, `keys`, `verified_cardinality`, `orphan_rate`, `query_used`), star-schema notes, and materialization candidates.
3. A "Skill gaps" section in the session summary.

## Acceptance Criteria
- [ ] 8 profile files plus `data_model_summary.md` exist.
- [ ] Every expected relationship above appears in the join table with a `verified_cardinality` value and the query that verified it.
- [ ] Only owned paths changed; no writes to any catalog.

## Owned Paths / Assets
- `examples/tpch/docs/data_profiles/**`
- Read-only: `samples.tpch.*`

## Dependencies
- Session 05a: EDA skill. Session 09: scaffold.
