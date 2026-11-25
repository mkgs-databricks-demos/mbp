# Session 10b (wave 0-4): TPC-H Deep EDA

* Mode: edit (allow_execute) | Branch: mg-genie-ontology-modeled-knowledge-sdk (verified read-only) | Plan: docs/plans/build-0/10b_tpch_deep_eda.md
* Skill followed: `skills/ontology-deep-eda/SKILL.md`

## What was done
* Profiled all 8 `samples.tpch` tables with read-only SQL on serverless (DESCRIBE, DESCRIBE DETAIL, DESCRIBE HISTORY, count, null/distinct, top values, min/max/avg, grain test, information_schema constraints, system lineage and usage).
* `lineitem` (29,999,795 rows) is the only table over the 10M threshold: null rates and distributions from `TABLESAMPLE (1 PERCENT) REPEATABLE (42)` (299,998 rows), `approx_count_distinct` on the full table. Every grain and join check ran exactly on full tables.
* Verified 10 joins with patterns D (orphans) and G (cardinality): every expected relationship from plan 10b, plus `lineitem -> part` and `lineitem -> supplier`. All are `many_to_one` with orphan_rate 0.0.

## Key findings
* Grains: all declared keys are unique (pattern C returned 0 rows), including composites `lineitem (l_orderkey, l_linenumber)` and `partsupp (ps_partkey, ps_suppkey)`.
* 250,011 of 750,000 customers (33.3%) have no orders; 1,950 of 4,000,000 partsupp offers have no line items. Counts of these entities must come from their own tables.
* Fan-out risks: `o_totalprice` through lineitem (up to 7 lines per order) and `ps_*` measures through lineitem (up to 26 lines per offer).
* `o_shippriority` is constant 0. No declared PK/FK constraints in `samples.information_schema`.
* Cadence: static data rebuilt by CREATE OR REPLACE TABLE AS SELECT (last 2026-09-14), followed by VACUUM-only commits.
* System tables were available (lineage and usage). Downstream table names were omitted because they are workspace-specific (mbp rule).

## Files created
* examples/tpch/docs/data_profiles/{customer,orders,lineitem,part,partsupp,supplier,nation,region}.md
* examples/tpch/docs/data_profiles/data_model_summary.md

## Checks
* 8 profiles + data_model_summary.md exist (directory listing): pass
* Every expected relationship from plan 10b is in `## Joins` with `verified_cardinality` and one-line `query_used` (read back from the file): pass
* Only owned paths changed; read-only SQL only; no catalog writes, no Git commands: pass
* No `parse` check of the summary through an SDK parser was run (none is required by plan 10b)

## Skill gaps (ontology-deep-eda)
1. Pattern F usage uses `LIKE '%<schema>.<table>%'`, so `tpch.part` also matches `tpch.partsupp`, which overcounts prefix-sharing tables. Suggest a word-boundary regex (`rlike '<schema>\\.<table>([^a-z0-9_]|$)'`).
2. Pattern E lineage on widely shared sources (`samples`) returns other workspaces' or users' downstream tables. The skill should say to report counts only and never names (the mbp / no-identifiers rule).
3. There is no guidance for the reverse direction of pattern D (right keys never referenced, e.g. customers without orders), which is what drives the most important metric-view caveat here. Add a "pattern D2: unreferenced right keys" with a LEFT ANTI JOIN.
4. Extracting "common filter/join columns" from usage samples is underspecified. A 400-statement sample was dominated by key lookups and produced no `JOIN ... ON` columns. Suggest a defined parser or dropping the step when the sample is not diverse.
5. `hot_table` "top quartile" on 8 tables is ambiguous (top 2). State the rounding rule.
6. The skill has no rule for which columns count as sensitive beyond examples. `o_clerk` and `p_name` were treated as text and their values withheld.
7. Update cadence: `DESCRIBE HISTORY LIMIT 20` may show only VACUUM commits on maintained tables. Suggest filtering out maintenance operations to find the last data write.

## Requests
* None. Session 11 (metric view synthesis) should read the fan-out and unreferenced-key flags in data_model_summary.md.
