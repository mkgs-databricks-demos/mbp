# Session 42 (wave 1-14): Independent report-perspective simulation of the TPC-H agent

Date: 2026-11-26. Build run 829522414538457. Mode: edit (allow_execute). Branch `mg-genie-ontology-build-1-plan` (checked with Git status, read-only; clean, no Git writes).

## Result

* 4 report personas, 10 turns each, each report asked as **one** Genie conversation against the dev `tpch_supply_chain_agent` space.
* **Overall score 83.75%** (33 correct, 1 partial, 3 wrong, 3 no_answer over 40 turns). Per report: exec 75.0%, regional 80.0%, procurement 90.0%, fulfillment 90.0%. The 80% target is met by turn score, but 0 of 4 assembled reports could be sent as-is.
* Ground truth: 40/40 statements over `samples.tpch` base tables, state SUCCEEDED, run 18:45:06Z-18:46:18Z, before the first Genie conversation started at 18:46:39Z.

## Independence rules (followed)

No file under `examples/tpch/docs/tuning/` was read, and no agent instructions, example SQL or benchmarks were read (the agent `.geniespace.json` was never opened, and session 41's summary was skipped on purpose because it describes tuning changes). Metric view YAML was not read either.

Files read for this session: `docs/plans/waves.json` (wave 1-14 entry and the top level), `docs/plans/build-1/42_report_simulation.md`, `PROJECT_MEMORY.md`, `examples/tpch/docs/domain_manifest.yml`, `examples/tpch/docs/deployment/agent_validation.md`, and the glossary files `examples/tpch/docs/semantics/{revenue,profit,on_time_shipping_rate,return_rate,inventory_value,national_market_share,average_order_value,late_receipt,order_fulfillment_cycle_time,supply_cost}.md`. Directory listings of `.build-status/` and `examples/tpch/docs/` showed file names under `tuning/`, but no contents were opened. The space id was found with `GET /api/2.0/genie/spaces` (by title).

## Changes

* `examples/tpch/docs/evaluation/personas.md`: personas, briefs, glossary definitions used, rubric.
* `examples/tpch/docs/evaluation/ground_truth/{exec_quarterly_review,regional_sales_europe,procurement_supplier_profit,fulfillment_quality}.sql`: pre-registered SQL, one statement per turn, with the turn wording as a comment. md5 of each file equals the executed statement text.
* `examples/tpch/docs/evaluation/reports/*.md`: each report as Genie produced it, with per-turn grades, completeness and send-as-is verdict.
* `examples/tpch/docs/evaluation/report_simulation_results.md`: rubric, GT timestamps and statement ids, per-turn grades, scorecard, failure themes mapped to fix layers.

Assets: 4 Genie conversations created in the dev space (read-only Q&A); 40 read-only ground-truth statements on the space warehouse. Nothing else was created or changed.

## Failure themes (backlog input for session 45)

1. Fulfillment metric view has no order date or year (exec 9-10 refused).
2. Profit metric view has no supplier region (procurement 2 refused).
3. Revenue metric view has no customer-level dimension (regional 7 returned nations).
4. A nation filter was carried into a region-scoped follow-up (regional 8: France only).
5. Return rate basis drifted from quantity to line count in a follow-up (fulfillment 8).
6. Quarter shown as a timestamp (exec 8).

## Checks

* report_simulation: pass. 4 personas (within 4-5), 10 turns each (within 8-15), one conversation each, per-turn grades, per-report and overall scores in the results file.
* ground_truth: pass. 40/40 SUCCEEDED, every GT timestamp earlier than its report's conversation start; files written and md5-checked before the GT run.
* Score below 80%: not applicable (83.75%). The 0/4 send-as-is outcome and the themes above are still recorded for session 45.

## Requests

None. (Session 45 should list the six themes; this needs no file change outside this session's paths.)
