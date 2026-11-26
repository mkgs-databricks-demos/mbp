# Benchmark review and corrected rescore (build 1)

Owner review, 2026-11-26, after tuning converged (wave 1-13). The benchmark stayed frozen from the baseline through the last tuning iteration, so the tuning curve in [accuracy_history.json](accuracy_history.json) is comparable across iterations. Eleven questions were then corrected in [benchmark/](benchmark/); the final tuning eval run was re-graded offline with [benchmark_review/rescore_corrected_benchmark](benchmark_review/rescore_corrected_benchmark.ipynb).

## Scores (final tuning eval run `01f1e9bfb0df1b80b8150581a4dc3e1d`, iteration 5)

| Benchmark | Tuning split | Holdout |
|---|---|---|
| Frozen (as tuned; reproduces `accuracy_history.json`) | 181 / 191 = 94.8% | 41 / 42 = 97.6% |
| Corrected | 189 / 191 = 99.0% | 41 / 42 = 97.6% |
| Corrected, the 2 reworded questions excluded | 189 / 189 = 100% | 41 / 42 = 97.6% |

## Corrections

| Question | Split | Problem in the frozen benchmark | Correction | Rescore |
|---|---|---|---|---|
| f029, f030, f031 | tuning | asks for a percent; expected SQL returned a 0-1 fraction | `100 * MEASURE(...)`, `expected_answer` in percent | BAD -> GOOD |
| x078 | tuning | expected SQL added `profit_per_supplier` (and sorted by it), not asked for | column removed, sorted by nation | BAD -> GOOD |
| x101 | tuning | expected SQL added `quantity_per_customer`, not asked for | column removed | BAD -> GOOD |
| x045 | tuning | expected SQL added `line_items`, not asked for | column removed | BAD -> GOOD |
| x042 | tuning | asks only for the share; expected SQL added `line_items` and `on_time_lines`, and rounded | line status and share only | BAD -> GOOD |
| x070 | tuning | `ROUND(volume_share, 4)` on shares of about 0.04 kept 3 significant digits; Genie compares 4 | `ROUND` removed | NEEDS_REVIEW -> GOOD |
| x062 | tuning | "higher-than-average" is ambiguous (overall rate or mean of nation rates; the nation rates differ only in the 4th digit) | reworded to "higher than the overall rate across all nations"; `ROUND` removed | not rescored (reworded) |
| x032 | tuning | the expected answer was empty (no nation has more suppliers than ordering customers: fewest customers 19,771, most suppliers 2,065), so it could never grade GOOD | reworded to "For each nation, show the number of suppliers and the number of ordering customers" | not rescored (reworded) |
| x002 | holdout | "which region earns the most" expected all 5 regions | `LIMIT 1` | stays BAD offline (see below) |

Every corrected expected SQL was run against the dev metric views and returns rows. Only these 11 questions changed (233 questions, split assignment unchanged).

## How the rescore was graded

* The generated SQL from the eval run was executed again and compared with the corrected expected SQL: same column count, same rows in any order, numbers to 4 significant digits.
* Checked against Genie's own verdicts on the 222 unchanged GOOD/BAD questions: 193 agree, 29 disagree, and all 29 are Genie GOOD / offline BAD (Genie accepted extra columns and small rounding differences). The offline grader is therefore stricter than Genie, so an offline GOOD is a safe lower bound.
* x002 stays BAD offline only because the agent returned 4 columns (`revenue` and `order_count` besides the answer). Genie tolerated extra columns elsewhere in this run, so a Genie re-evaluation may grade it GOOD; the holdout is reported at the frozen 41 / 42.
* x032 and x062 changed wording, so the agent's old answers do not apply; they need a new evaluation (the next benchmark sync to the Genie space, build 2).

The Genie space still holds the frozen benchmark; nothing was deployed for this review.
