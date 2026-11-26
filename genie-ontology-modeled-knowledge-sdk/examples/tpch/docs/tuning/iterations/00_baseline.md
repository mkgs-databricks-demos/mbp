# Tuning iteration 0: baseline

| Metric | Value |
|---|---|
| Eval run | 01f1e95a7f2e12baa07333ab54feff30 |
| Started | 2026-11-26T05:30:31+00:00 |
| Tuning accuracy | 83.8% (160/191) |
| Holdout accuracy | 83.3% (35/42) |
| Next plan | docs/tuning/tuning_plan_01.md |
| Asymptote reached | no |
| Stop rule | 0 tuning plan(s) applied; the stop rule needs at least 3 |
| Last deltas (pp) | [] |
| Holdout gap (pp) | 0.0 |

## Changes

_None._

## Tuning failures

Holdout failures are not listed.

| ID | Question | SQL succeeded | Unit mismatch | Needs review | Error |
|---|---|---|---|---|---|
| f031 | What percentage of lines shipped by REG AIR came back? | yes | no | no |  |
| s036 | What fraction of gross sales was given up through discounts? | yes | no | no |  |
| f051 | What profit was earned on parts whose name contains a color word that no part uses, such as 'plaid'? | yes | no | no |  |
| s040 | What net revenue is on lines that are still open (line status O) but were ordered before 1995? | yes | no | no |  |
| s059 | What national market share did suppliers from CHINA hold in the ASIA customer region across all years? | yes | no | no |  |
| f029 | What percent of order lines were returned overall? | yes | no | no |  |
| x028 | Year over year, how did the change in profit compare with the change in order count? | yes | no | no |  |
| x003 | By market segment, compare the total order price on order headers with the net revenue from line items. | yes | no | no |  |
| x017 | Compare high-priority orders with all other orders: order count and average fulfillment cycle in days. | yes | no | no |  |
| x023 | In 1996, what was the market volume per order for each customer nation? | yes | no | no |  |
| x014 | For each order quarter of 1993, show the order count and the share of order lines that were returned. | yes | no | no |  |
| x046 | By ship mode, show the average discount next to the average transit days. | yes | no | no |  |
| f002 | What share of order lines shipped on or before their commit date, across all data? | yes | no | no |  |
| x062 | Which customer nations have a higher-than-average refund rate on lines, and what is their market volume? | yes | no | yes |  |
| x032 | Are there any nations with more suppliers than ordering customers? | yes | no | no |  |
| x078 | By supplier nation, show profit and the number of suppliers. | yes | no | no |  |
| x058 | For air shipments only (AIR and REG AIR), show the return line rate and the on-time shipping rate. | yes | no | no |  |
| x097 | By order year, show net revenue, returned revenue and profit, and profit after subtracting returned revenue. | yes | no | no |  |
| x034 | For each market segment, what fraction of net revenue was returned? | yes | no | no |  |
| s052 | What was BRAZIL's national market share of ECONOMY ANODIZED STEEL volume in the AMERICA customer region, by year for ... | yes | no | no |  |
| x042 | By line status, what share of line items shipped on time? | yes | no | no |  |
| f034 | How much returned revenue is on lines whose return flag is N (not returned)? | yes | no | no |  |
| x070 | Which supplier nation earns the most profit, and what share of total market volume do its suppliers have? | yes | no | no |  |
| f030 | What is the return rate for the AUTOMOBILE market segment, in percent? | yes | no | no |  |
| x045 | On ship date 1996-06-03, how much net revenue shipped and how many of those lines shipped on time? | yes | no | no |  |
| s053 | What share of total market volume does each customer region account for? | yes | no | no |  |
| f011 | What is the on-time shipping rate for lines shipped by AIR, as a fraction? | yes | no | yes |  |
| x101 | By order year, show the number of ordering customers and the quantity sold in the profit view. | yes | no | no |  |
| x054 | Show the margin trend: profit margin and average discount by order year. | yes | no | no |  |
| s058 | What was market volume for orders placed in 1999? | yes | no | no |  |
| x093 | Month by month in 1995, show orders placed, net revenue and returned revenue. | yes | no | no |  |

## Breakdown (tuning split)

Holdout is reported as the overall number only. Per-view and per-type rows overlap: a question with two views or two `type:` tags counts in each.

| Metric view | n | correct | accuracy | delta |
|---|---|---|---|---|
| mv_tpch_supply_chain_fulfillment | 31 | 24 | 77.4% | — |
| mv_tpch_supply_chain_market_share | 35 | 28 | 80.0% | — |
| mv_tpch_supply_chain_orders | 52 | 44 | 84.6% | — |
| mv_tpch_supply_chain_profit | 39 | 32 | 82.1% | — |
| mv_tpch_supply_chain_returns | 45 | 35 | 77.8% | — |
| mv_tpch_supply_chain_revenue | 56 | 46 | 82.1% | — |
| mv_tpch_supply_chain_supply_cost | 28 | 26 | 92.9% | — |

| Type | n | correct | accuracy | delta |
|---|---|---|---|---|
| breakdown | 42 | 39 | 92.9% | — |
| cross_view | 83 | 65 | 78.3% | — |
| edge | 35 | 26 | 74.3% | — |
| filter | 30 | 26 | 86.7% | — |
| ratio | 30 | 17 | 56.7% | — |
| simple | 18 | 17 | 94.4% | — |
| synonym | 20 | 18 | 90.0% | — |
| time | 32 | 27 | 84.4% | — |

## Failures by category (tuning split, 31)

| Category | Count | Question ids |
|---|---|---|
| Unit / format | 11 | s036, f002, s053, x042, x034, s059, s052, x014, x070, x046, x054 |
| Benchmark defect | 6 | f029, f030, f031, x078, x101, x045 |
| Filter / edge | 7 | f051, s040, f034, s058, f011, x097, x058 |
| Missing measure | 1 | x023 |
| Ambiguity | 6 | x003, x017, x028, x032, x062, x093 |

`needs_review` (counted as misses): x062, f011. `unit_mismatch`: 0 flagged, because the eval-run result details did not include result rows (0 rows on all 31 failures), so `_unit_mismatch` could not compare values. The Unit / format category was assigned from the generated SQL (`100 *` on a 0-1 ratio where the question asks for a fraction or share).

## Question movement (tuning split)

Baseline: no previous iteration.

## Benchmark defects

Reported for the owner; not tuned, benchmark not edited (frozen after the baseline).

| Question id | Problem with the expectation |
|---|---|
| f029 | asks "what percent"; expected SQL returns a 0-1 fraction |
| f030 | asks "in percent"; expected SQL returns a 0-1 fraction |
| f031 | asks "what percentage"; expected SQL returns a 0-1 fraction |
| x078 | asks for profit and supplier count; expected SQL adds a `profit_per_supplier` column not asked for |
| x101 | asks for customers and quantity; expected SQL adds `quantity_per_customer` not asked for |
| x045 | asks for revenue and on-time lines; expected SQL adds `line_items` not asked for |

## Scoring definition

Quoted from the `benchmark.py` module docstring, "Scoring definition": **accuracy** = `matches_expected / with_expectations` when `with_expectations > 0` (`accuracy_basis = "expected"`), else `sql_succeeded / total`. Per split, `Summary.tuning` and `Summary.holdout` are `{n, correct, accuracy}` over the results with expectations in that split. For evaluation runs, the verdict is the result's `assessment` (`GOOD` = match); `needs_review` counts as not matched.

## Evaluation method

eval run 01f1e95a7f2e12baa07333ab54feff30 (Genie benchmark evaluation run on the deployed dev agent, all 233 benchmarks, both splits; status DONE, 233/233 results mapped to question ids; API totals num_correct 195, num_needs_review 2). Run started 2026-11-26T05:30:31+00:00, after build run 829522414538457 started (2026-11-26T05:25:43Z). An earlier eval run from build run 629243800379582 is not used because it predates this build run.
