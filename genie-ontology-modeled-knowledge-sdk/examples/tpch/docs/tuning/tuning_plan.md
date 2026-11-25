# Tuning Plan — tpch_supply_chain

Rule: metric views first, agent instructions last. Max 2 fix iterations.
Gate: accuracy >= 70% per agent (definition: see benchmark_results.md).

## Agents

| Agent | Space id source | Metric views | Baseline accuracy | Final accuracy | Gate |
|---|---|---|---|---|---|
| tpch_supply_chain_agent | docs/deployment/agent_validation.md (session 15) | 7 | 93.3% | 93.3% | pass |

The gate passed at baseline (14/15), so no fix iteration ran, following the `ontology-tuning` rule to stop early once the gate passes. No metric view YAML and no `.geniespace.json` changed, so neither bundle was redeployed and `register_metric_views` was not re-run.

## Phase 1 — Metric view actions

None applied in build 0. Proposed (not applied; see Remaining items):

| # | Question id(s) | Category | Metric view | Change | Iteration |
|---|---|---|---|---|---|
| 1 | q11 | Ambiguity (ratio unit) | mv_tpch_supply_chain_returns | Add `format: {type: percentage}` to `Return Rate` and `Return Line Rate`, and say "fraction 0-1" in their comments, so Genie stops rescaling the value to 0-100 in SQL | proposed for build 1 |

## Phase 2 — Agent actions (only when Phase 1 cannot fix it)

None. No failure needed an agent instruction, and the synonym questions (bookings, AOV, order cycle time, stock value) resolved through metric view metadata alone.

## Iteration log

| Iteration | Agent | Failures before | Fixes applied | Accuracy before -> after |
|---|---|---|---|---|
| baseline | tpch_supply_chain_agent | 1 (q11) | — | — -> 93.3% |

## Remaining items

| Question id | Category | Recommended next fix | Owner |
|---|---|---|---|
| q11 | Ambiguity (ratio unit) | Phase 1 #1 (percentage format + comment on returns ratios), then re-register and re-run q11. Also consider having `benchmark.score` accept a x100 percentage of a 0-1 expected ratio, flagged as `unit_mismatch` rather than a miss | build 1 tuning |
| all | Interpretation | Fill in the empty Interpretation column in benchmark_results.md (human or judge review) | owner |

## Build 1 tuning backlog

Accuracy is above 70%, so the build-0 threshold policy needs no backlog. The two items above are the only open items.
