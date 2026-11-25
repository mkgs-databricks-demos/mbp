# Session 26: Exhaustive Tuning Protocol Skill & Skills Index (R8)

## Scope
Rewrite `skills/ontology-tuning` for the exhaustive protocol, write the protocol design doc, and write `skills/README.md` for all six skills.

## Context
* Owner request (2026-11-25), protocol table in [INDEX](INDEX.md#exhaustive-tuning-protocol-owner-request): 100-498 questions, coverage over every metric view, measure and dimension, >= 25% cross-view, a 20% holdout, at least three tuning plans, stop only at the asymptote, MV-first: instructions or example SQL only when all Unity Catalog semantic options are exhausted, and an independent report-perspective simulation as the final evaluation.
* The current skill (10-20 questions, at most 2 iterations, 70% gate) is replaced, not extended. Keep its triage categories.
* Library: session 22's `benchmark` API and constants; quote them, do not restate numbers that could drift (reference the constants by name and give their build-1 values once).

## Tasks
1. `skills/ontology-tuning/SKILL.md` + `references/`:
   * benchmark authoring: one YAML file per view group plus a cross-view file, tag schema, tokenized `expected_sql` that ran `SUCCEEDED`, wording different from the agent's sample questions;
   * coverage check (`gos-benchmark coverage`) before any evaluation;
   * evaluation via Genie benchmark eval runs, fallback `run_benchmark`;
   * triage of **tuning-split** failures only; holdout results are read as numbers, never as question text;
   * the fix ladder (steps 1-8 metric view / glossary / Pages, then 9 instruction, 10 example SQL), with an exhaustion record per failure before steps 9-10: `{question_id, category, tried: [{step, iteration, result}]}`;
   * tuning plan template (`tuning_plan_<k>.md`): actions grouped by metric view, ladder step, expected effect, status (`planned`/`applied`/`reverted`) and outcome;
   * iteration loop and the asymptote stop rule (`benchmark.asymptote`); conditional iterations that record `converged at iteration <j>` and change nothing;
   * `tuning_summary.md` template (accuracy curve, changes by ladder step, remaining failures);
   * the report simulation method (personas, pre-registered ground truth on source tables, one conversation per report, grading rubric) for an **independent** session.
2. `docs/design/tuning-protocol.md`: rationale (why holdout, why the asymptote over a fixed count, why MV-first), the numbers, and how the run kit uses it.
3. `skills/README.md`: each skill, its stage, the platform skills it relies on, precedence when both load (SDK skill for SDK rules, platform skill for syntax), and the Unity Catalog id it is published under (session 27 fills the ids; leave the column with the planned snake_case ids).

## Acceptance Criteria
- [ ] Gate check `skills_reconciled` passes (README lists six skills; tuning description names the SDK tuning stage).
- [ ] The skill contains no fixed "at most 2 iterations" or "10-20 questions" rule.
- [ ] Every number in the skill matches a `benchmark` constant from session 22.

## Owned Paths
- `skills/ontology-tuning/**`, `skills/README.md`, `docs/design/tuning-protocol.md`

## Dependencies
- Session 22 (benchmark API). Overlap notes from sessions 24, 25 arrive in the same wave: write README rows for their skills from the skill files themselves.
