# Session 42: Independent Report-Perspective Simulation (Final Evaluation)

## Scope
Evaluate the tuned TPC-H agent the way business users would use it to build reports: several personas, each producing one report through a multi-turn Genie conversation, graded against ground truth computed independently from the source tables. This is the build-1 final evaluation.

## Context
* Owner request (2026-11-25): an independent simulation of using the Genie Agent from a report perspective, as the final evaluation.
* **Independence rules.** Do not read anything under `examples/tpch/docs/tuning/`, and do not read the agent file's instructions, example SQL or benchmarks. You may read: `examples/tpch/docs/research/`, `docs/semantics/`, `docs/data_profiles/`, `docs/domain_manifest.yml`, and `docs/deployment/` (space id). Ground truth comes from `samples.tpch` source tables, **not** the metric views, so a metric view defect cannot hide itself.
* Benchmarks ask one question per conversation; reports test what benchmarks cannot: follow-ups that rely on earlier turns, drill-downs, period comparisons, and assembling a narrative.
* Target: 80% overall. Recorded, not gated: a lower score becomes a build-1 backlog item (session 45 lists it).

## Tasks
1. Personas (4-5), each with a report brief in `examples/tpch/docs/evaluation/personas.md`, for example: executive quarterly supply-chain review; regional sales manager (nation/region drill-down); procurement lead (supplier cost and profit); fulfillment/quality lead (shipping performance and returns); finance analyst (revenue vs cost, cross-view).
2. For each report, 8-15 turns written **before** asking Genie, including at least 3 follow-ups that depend on earlier turns ("now only for Europe", "and the same for the prior year").
3. Pre-register ground truth: for each turn, SQL over `samples.tpch` source tables in `examples/tpch/docs/evaluation/ground_truth/<report>.sql`, run read-only (`SUCCEEDED`), results and timestamps recorded before the Genie run.
4. Run each report as **one** Genie conversation (`start_conversation`, then follow-up messages); capture SQL, results and text per turn.
5. Grade each turn: `correct` (numbers within 1e-4 relative tolerance, right grain and filters), `partial` (right numbers, wrong presentation or a missing part), `wrong`, `no_answer`; plus per report: completeness and whether the assembled narrative could be sent as-is (yes/no with reason).
6. Write `examples/tpch/docs/evaluation/reports/<report>.md` (the report as Genie produced it) and `report_simulation_results.md` (rubric, per-turn grades, per-report score = correct + 0.5 x partial over turns, overall score, failure themes mapped to likely fix layers: metric view, glossary, agent).

## Acceptance Criteria
- [ ] Gate checks `report_simulation` and `ground_truth` pass.
- [ ] Summary states the independence rules were followed (files read listed).

## Owned Paths
- `examples/tpch/docs/evaluation/**`

## Dependencies
- Session 41 (tuned agent).
