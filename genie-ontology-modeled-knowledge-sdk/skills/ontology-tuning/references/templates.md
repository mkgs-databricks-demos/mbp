# Tuning Templates

Templates for `ontology-tuning`. Copy the matching block into the run project and fill it in. Keep identifiers tokenized (`${target_catalog}.${target_schema}`). Thresholds are the `benchmark` constants; name them, do not copy their values into run files.

## Layout

```
docs/tuning/
  benchmark/<group>.yml          # one per view group, frozen after the baseline
  benchmark/cross_view.yml
  accuracy_history.json          # benchmark.append_history
  iterations/00_baseline.md      # benchmark.write_iteration_md, then <kk>.md per iteration
  tuning_plan_<kk>.md            # written by iteration k-1, applied by iteration k
  tuning_summary.md              # written by the last iteration
```

## `docs/tuning/benchmark/<group>.yml`

```yaml
# View group: <group> (metric views: mv_<domain>_<process>, ...)
# expected_sql checked SUCCEEDED on <YYYY-MM-DD> (rendered tokens, read-only)
- id: sales_001
  question: "How much did we book in net sales during 1995?"
  expected_sql: |
    SELECT MEASURE(`Net Revenue`) AS net_revenue
    FROM ${target_catalog}.${target_schema}.mv_<domain>_sales
    WHERE `Order Year` = 1995
  tags: [type:synonym, view:mv_<domain>_sales, measure:Net Revenue, dimension:Order Year]
- id: sales_002
  question: "Net sales by market segment for 1996, highest first"
  expected_sql: |
    SELECT `Market Segment`, MEASURE(`Net Revenue`) AS net_revenue
    FROM ${target_catalog}.${target_schema}.mv_<domain>_sales
    WHERE `Order Year` = 1996
    GROUP BY ALL ORDER BY net_revenue DESC
  tags: [type:breakdown, view:mv_<domain>_sales, measure:Net Revenue, dimension:Market Segment, dimension:Order Year]
```

`cross_view.yml` uses `type:cross_view` (or another type with two or more `view:` tags) and qualified tags (`measure:mv_<domain>_sales.Net Revenue`) where names collide.

## `docs/tuning/tuning_plan_<kk>.md`

~~~markdown
# Tuning Plan <kk> — <agent>

Written by: iteration <k-1> (<YYYY-MM-DD>), from the tuning-split failures in iterations/<k-1>.md.
Applied by: iteration <k>.
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only.

## Actions by metric view

### mv_<domain>_<process>

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | sales_014, sales_031 | Synonym gap | 2 synonyms | add "bookings" to Net Revenue | both answer with Net Revenue | planned | |
| 2 | sales_052 | Filter / edge | 5 FILTER | exclude returned lines from Net Revenue | totals match | planned | |

### Glossary / UC Pages

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|

### Agent (steps 9-10, exhaustion record required)

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

```json
[{"question_id": "<id>", "category": "<category>",
  "tried": [{"step": 1, "iteration": 1, "result": "still failing"}]}]
```

## Reverts carried from the previous iteration

| Action | Why reverted | Questions it regressed |
|---|---|---|

## Benchmark defects (for the owner, not tuned)

| Question id | Problem with the expectation |
|---|---|
~~~

Status values: `planned` (when written), then `applied` or `reverted` (by the applying iteration) with a one-line outcome.

## `docs/tuning/iterations/<kk>.md`

`benchmark.write_iteration_md` writes the accuracy, changes, stop-rule state and tuning-split failures. Append:

```markdown
## Breakdown (tuning split)

| Metric view | n | correct | accuracy | delta |
|---|---|---|---|---|

| Type | n | correct | accuracy | delta |
|---|---|---|---|---|

## Question movement (tuning split)

| Fixed | Regressed | Still failing |
|---|---|---|
| <ids> | <ids> | <ids> |

## Benchmark defects

## Evaluation method

eval run <id> | fallback run_benchmark (reason)
```

Iterations that start converged contain only: `converged at iteration <j>` and the `benchmark.asymptote` output.

## `docs/tuning/tuning_summary.md`

```markdown
# Tuning Summary — <agent>

## Result

Stop rule: reached at iteration <j> | exhausted after MAX_FIX_ITERATIONS (<reason from benchmark.asymptote>).

## Accuracy curve

| Iteration | Label | Tuning accuracy | Delta (pp) | Holdout accuracy | Holdout gap to best (pp) |
|---|---|---|---|---|---|
| 0 | baseline | | — | | |

## Changes by ladder step

| Step | Layer | Iterations | Actions applied | Actions reverted |
|---|---|---|---|---|
| 1 | metric view comment | | | |
| ... | | | | |
| 9 | agent instruction | | | |
| 10 | agent example SQL | | | |

## Agent-layer changes

| Change | Question ids | Why the metric view / glossary steps were not enough (exhaustion record) |
|---|---|---|

## Remaining tuning-split failures

| Question id | Category | Steps tried | Recommended next fix |
|---|---|---|---|

## Benchmark defects reported
```
