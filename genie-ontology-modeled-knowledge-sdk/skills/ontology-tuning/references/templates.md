# Tuning Templates

Templates for `ontology-tuning`. Copy the matching block into the run project and fill it in. Keep identifiers tokenized (`${target_catalog}.${target_schema}`).

## `docs/tuning/tuning_plan.md`

```markdown
# Tuning Plan — <domain_name>

Rule: metric views first, agent instructions last. Max 2 fix iterations.
Gate: accuracy >= 70% per agent (definition: see benchmark_results.md).

## Agents

| Agent | Space id source | Metric views | Baseline accuracy | Final accuracy | Gate |
|---|---|---|---|---|---|
| <agent> | docs/deployment/<file> | <n> | <x>% | <y>% | pass/fail |

## Phase 1 — Metric view actions

| # | Question id(s) | Category | Metric view | Change (synonym / comment / display_name / measure / filter / join) | Iteration |
|---|---|---|---|---|---|
| 1 | q03, q11 | Synonym gap | mv_<domain>_<process> | add synonym "bookings" to Revenue | 1 |

## Phase 2 — Agent actions (only when Phase 1 cannot fix it)

| # | Question id(s) | Category | Agent | Change (text instruction / example SQL / join spec) | Why a metric view change was not enough |
|---|---|---|---|---|---|

## Iteration log

| Iteration | Agent | Failures before | Fixes applied | Accuracy before -> after |
|---|---|---|---|---|
| baseline | <agent> | <n> | — | — -> <x>% |
| 1 | <agent> | <n> | Phase 1 #1-#4 | <x>% -> <y>% |
| 2 | <agent> | <n> | ... | <y>% -> <z>% |

## Remaining items

| Question id | Category | Recommended next fix | Owner |
|---|---|---|---|
```

## `docs/tuning/benchmark_results.md`

The per-question table comes from `benchmark.write_results_md(summary, results, path)`. Add these sections around it:

```markdown
# Benchmark Results — <domain_name>

## Accuracy definition

> <quote the scoring definition from the benchmark.py docstring verbatim>

## Summary

| Agent | Questions | With expectation | SQL generated | SQL succeeded | Matches expected | Accuracy (baseline) | Accuracy (final) |
|---|---|---|---|---|---|---|---|
| <agent> | <n> | <n> | <n> | <n> | <n> | <x>% | <y>% |

## Results (final run)

<output of benchmark.write_results_md>

## Iteration history

| Run | Date | Agent | Accuracy |
|---|---|---|---|
| baseline | <YYYY-MM-DD> | <agent> | <x>% |
| iteration 1 | <YYYY-MM-DD> | <agent> | <y>% |
```

## `docs/tuning/benchmark_questions.yml`

```yaml
- id: q01
  question: "What was total revenue in 1995?"
  expected_sql: |
    SELECT MEASURE(`Revenue`) AS revenue
    FROM ${target_catalog}.${target_schema}.mv_<domain>_orders
    WHERE YEAR(`Order Date`) = 1995
  tags: ["agent:<agent>", simple]
- id: q02
  question: "Which market segment brings in the most sales?"
  tags: ["agent:<agent>", synonym, breakdown]
  expected_answer: "<value from a read-only query>"
```
