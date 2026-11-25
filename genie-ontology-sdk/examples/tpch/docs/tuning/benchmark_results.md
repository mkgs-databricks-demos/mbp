# Benchmark Results — tpch_supply_chain

Session 16 (wave 0-9, build 0), run `440901917884797`, 2026-11-25. Agent: `tpch_supply_chain_agent` (dev deployment from session 15; space id in `docs/deployment/agent_validation.md` / `bundle summary`, not repeated here). Questions: [benchmark_questions.yml](benchmark_questions.yml). Identifiers are tokenized as `${target_catalog}.${target_schema}`.

## Accuracy definition

> **accuracy** = ``matches_expected / with_expectations`` when ``with_expectations > 0`` (``accuracy_basis = "expected"``), else ``sql_succeeded / total`` (``accuracy_basis = "succeeded"``); 0.0 for an empty run. The tuning gate is ``accuracy >= 0.70`` (``ACCURACY_GATE``).
>
> **matches_expected**: [...] ``expected_answer`` is a scalar: some cell of the first result row equals it; [...] When both are given, ``expected_answer`` is used. Values are compared after normalization: numbers with relative tolerance 1e-4 (absolute 1e-6), other values as trimmed, case-insensitive strings, ``NULL`` as ``None``.

(Quoted from the `genie_ontology_sdk/benchmark.py` module docstring.) Every question has a scalar `expected_answer`, so the basis is `expected`.

## Summary

| Agent | Questions | With expectation | SQL generated | SQL succeeded | Matches expected | Errors | Accuracy (baseline) | Accuracy (final) |
|---|---|---|---|---|---|---|---|---|
| tpch_supply_chain_agent | 15 | 15 | 15 | 15 | 14 | 0 | 93.3% | 93.3% (baseline is final) |

Gate (>= 70%): **pass at baseline**. Per the `ontology-tuning` skill ("Stop earlier when the gate passes"), no fix iteration was run, so no metric view or agent file changed in this wave.

## Results (baseline = final run)

From `benchmark.write_results_md` (Interpretation column left for human review):

| ID | Question | SQL generated | SQL succeeded | Matches expected | Interpretation | Tags |
|---|---|---|---|---|---|---|
| q01 | What was total net revenue for orders placed in 1995? | yes | yes | yes |  | simple |
| q02 | How much were total bookings in 1996? | yes | yes | yes |  | synonym, simple |
| q03 | Which customer region generated the most net revenue in 1994? | yes | yes | yes |  | breakdown |
| q04 | What was the AOV in 1997? | yes | yes | yes |  | ratio, synonym |
| q05 | How many high-priority orders were placed in 1993? | yes | yes | yes |  | filter |
| q06 | In which year were the most orders placed? | yes | yes | yes |  | time, breakdown |
| q07 | What was the on-time delivery rate for line items received in 1996? | yes | yes | yes |  | ratio, time |
| q08 | What is the average order cycle time in days? | yes | yes | yes |  | synonym, simple |
| q09 | What was the overall profit margin in 1996? | yes | yes | yes |  | ratio |
| q10 | Which supplier region holds the largest stock value? | yes | yes | yes |  | synonym, breakdown |
| q11 | What share of shipped quantity was returned for AUTOMOBILE segment customers? | yes | yes | **no** |  | filter, ratio |
| q12 | What was net revenue in August 1998, the last month with orders? | yes | yes | yes |  | edge, time |
| q13 | In 1996, what fraction of market volume for ASIA customers was supplied by Chinese suppliers? | yes | yes | yes |  | ratio, filter |
| q14 | How much revenue was given up through discounts on orders from 1994? | yes | yes | yes |  | synonym, simple |
| q15 | How many distinct customers placed at least one order in 1995? | yes | yes | yes |  | simple, filter |

All questions carry the tag `agent:tpch_supply_chain_agent` (omitted above).

### Failure detail: q11

Generated SQL (tokenized):

```sql
SELECT 100 * MEASURE(`Return Rate`) AS `returned_share_pct`
FROM ${target_catalog}.${target_schema}.mv_tpch_supply_chain_returns
WHERE `Market Segment` ILIKE '%AUTOMOBILE%'
GROUP BY ALL
```

Result `24.687630` vs expected `0.2468763007`. The measure and the filter are right; Genie scaled the 0-1 fraction to a percentage, so the scalar comparison fails. The text answer ("24.69%") is correct. Triage: ambiguity (unit of a ratio measure); see `tuning_plan.md`.

Observations on passing questions: synonyms resolved without agent instructions ("bookings" -> `Order Total Price`, "AOV" -> `Average Order Value`, "order cycle time" -> `Average Fulfillment Cycle Days`, "stock value" -> `Inventory Value`). q04 picked the line-item `Average Order Value` over the header `Average Order Total`, as the measure comments intend.

## Expected answers (read-only SQL over `samples.tpch`)

| ID | Expected | Query |
|---|---|---|
| q01 | 165028893111.8535 | `SUM(l_extendedprice*(1-l_discount))` from lineitem JOIN orders, `YEAR(o_orderdate)=1995` |
| q02 | 172605588830.66 | `SUM(o_totalprice)` from orders, `YEAR(o_orderdate)=1996` |
| q03 | MIDDLE EAST | net revenue by `r_name` (lineitem-orders-customer-nation-region), 1994, top 1 (33306039465.3013; EUROPE second at 33195877085.1033) |
| q04 | 145293.9571 | net revenue / `COUNT(DISTINCT l_orderkey)`, order year 1997 |
| q05 | 455364 | `COUNT(*)` orders, 1993, `o_orderpriority IN ('1-URGENT','2-HIGH')` |
| q06 | 1996 | `COUNT(*)` orders by `YEAR(o_orderdate)`, top 1 (1141556) |
| q07 | 0.3677598081618798 | `1 - COUNT_IF(l_receiptdate>l_commitdate)/COUNT(*)`, `YEAR(l_receiptdate)=1996` |
| q08 | 76.49805303669575 | `AVG(DATEDIFF(l_receiptdate, o_orderdate))` over lineitem JOIN orders |
| q09 | 0.648703 | (net revenue - `SUM(ps_supplycost*l_quantity)`) / net revenue, lineitem-orders-partsupp on (partkey, suppkey), 1996 |
| q10 | ASIA | `SUM(ps_supplycost*ps_availqty)` by supplier `r_name`, top 1 |
| q11 | 0.2468763007 | `SUM(l_quantity) FILTER (WHERE l_returnflag='R') / SUM(l_quantity)`, `c_mktsegment='AUTOMOBILE'` |
| q12 | 909368702.339 | net revenue, `o_orderdate` in [1998-08-01, 1998-09-01) |
| q13 | 0.04 | CHINA-supplier net revenue / all net revenue, customer region ASIA, 1996 (exact 0.0400002) |
| q14 | 8702939704.3524 | `SUM(l_extendedprice*l_discount)`, order year 1994 |
| q15 | 432892 | `COUNT(DISTINCT o_custkey)` orders, 1995 |

## Iteration history

| Run | Date | Agent | Accuracy |
|---|---|---|---|
| baseline | 2026-11-25 | tpch_supply_chain_agent | 93.3% (14/15) |
| iteration 1 | — | — | not run: gate passed at baseline |
| iteration 2 | — | — | not run: gate passed at baseline |
