---
name: ontology-tuning
description: Genie Ontology Modeled Knowledge SDK tuning stage (wave 8). Load when a pipeline-run session must author the exhaustive benchmark set in docs/tuning/benchmark/, check coverage, run Genie benchmark evaluation runs on a tuning/holdout split, triage tuning-split failures, apply MV-first tuning plans (docs/tuning/tuning_plan_<kk>.md) until the benchmark.asymptote stop rule, write tuning_summary.md, or plan the independent report simulation. Not for general Genie space or metric view questions.
---

# Ontology Genie Agent Tuning

Measure how well the deployed Genie Agents of a Genie Ontology run answer business questions, then improve them with the smallest, most general fixes until accuracy stops improving. This skill holds only the SDK tuning rules; the numbers live in the SDK `benchmark` module and the reasoning in `docs/design/tuning-protocol.md`. Templates: [references/templates.md](references/templates.md). Final evaluation method: [references/report-simulation.md](references/report-simulation.md).

**Precedence.** For metric view YAML syntax load the platform `metric-views` skill; for Genie space file and API details, the SDK `geniespace` module and `ontology-agent-curation`. When both load, this skill wins on *what* to change and *when*; the platform skill wins on syntax. See `skills/README.md`.

## Protocol constants

Never hard-code these; read them from `genie_ontology_modeled_knowledge_sdk.benchmark`. Build-1 values, given once:

| Constant | Build-1 value | Meaning |
|---|---|---|
| `MIN_QUESTIONS` / `MAX_QUESTIONS` | 100 / 498 | questions per agent |
| `MAX_SPACE_BENCHMARKS` | 500 | Genie's benchmark limit per agent |
| `MIN_PER_VIEW` | 12 | questions per metric view |
| `MIN_CROSS_VIEW_SHARE` | 0.25 | share of questions tagged with two or more views |
| `HOLDOUT_SHARE` | 0.2 | deterministic holdout share |
| `MIN_FIX_ITERATIONS` | 3 | tuning plans that must be applied |
| `ASYMPTOTE_DELTA_PP` / `ASYMPTOTE_WINDOW` | 1.0 / 2 | stop when each of the last `ASYMPTOTE_WINDOW` iterations gained less than this (percentage points) |
| `HOLDOUT_TOLERANCE_PP` | 2.0 | latest holdout accuracy within this of its best |
| `MAX_FIX_ITERATIONS` | 6 | `asymptote` reports `exhausted` after this many plans |
| `QUESTION_TYPES` | `simple`, `breakdown`, `time`, `filter`, `ratio`, `synonym`, `edge`, `cross_view` | every type is used |

If the module values differ from this table, the module wins: update this table and say so in your summary. `ACCURACY_GATE` (`Summary.passes_gate`) is reported, not used to stop tuning.

## Rules

* **MV-first.** Fix Unity Catalog semantics (metric views, glossary, UC Pages) first, the agent last. An agent text instruction or example SQL is allowed only after an exhaustion record shows every applicable metric view and glossary step was tried for that failure (fix ladder below). Never add an instruction that restates metric view metadata; never add example SQL for a single-view, single-measure question.
* **Holdout is blind.** Tuning reads holdout results as numbers only (`Summary.holdout`, `accuracy_history.json`). Never open holdout question text, expected SQL or failures, and never triage them. `benchmark.write_iteration_md` already lists only tuning-split failures; do not work around it.
* **The benchmark is frozen after the baseline.** Do not edit `docs/tuning/benchmark/**` during tuning: a changed benchmark invalidates the accuracy curve. A wrong expectation is reported as `benchmark_defect` in the iteration file for the owner.
* **Stop at the asymptote, not at a count.** No fixed iteration limit and no accuracy gate ends tuning; `benchmark.asymptote` does.
* **Unattended sessions:** no Git commands, no file deletion; write only the paths your session owns; re-register or redeploy only when your session is approved to, otherwise record the redeploy as a request. Committed questions and SQL use the `${target_catalog}.${target_schema}` tokens, never workspace identifiers.

## 1. Inputs

| Input | Use it for |
|---|---|
| `docs/deployment/` (or the agents bundle `bundle summary`) | the deployed Genie space id of each agent |
| `docs/research/*.md` KPI definitions, `docs/semantics/*.md` | the questions and their business meaning |
| `ontology-metric-views/metric_views/**/*.yml` | measures, dimensions, synonyms, comments, filters (coverage targets) |
| `ontology-genie-agents/agents/*.geniespace.json` | sample questions (to avoid), instructions, example SQL, benchmarks |
| `docs/data_profiles/data_model_summary.md` | verified join cardinalities, for join triage |

## 2. Author the benchmark set

One folder per agent: `docs/tuning/benchmark/` (or `docs/tuning/benchmark/<agent>/` for several agents). **One YAML file per view group** (`<group>.yml`, ids prefixed by the file, e.g. `sales_001`) **plus one cross-view file** (`cross_view.yml`). Size between `MIN_QUESTIONS` and `MAX_QUESTIONS`.

Each question: `{id, question, expected_sql, expected_answer?, tags, split?}`. Tag schema (parsed by `benchmark.Question`):

| Tag | Rule |
|---|---|
| `type:<t>` | exactly one, from `QUESTION_TYPES` |
| `view:<mv>` | every metric view the answer needs (file stem of the YAML); two or more for `cross_view` |
| `measure:<m>` or `measure:<mv>.<m>` | every measure used (qualify when two views share a name) |
| `dimension:<d>` or `dimension:<mv>.<d>` | every dimension used, including filters and groupings |
| free labels | anything else (`persona:finance`, `kpi:<term>`) |

* **Expected SQL:** tokenized `MEASURE()` over the metric views. Render the tokens and run each statement read-only; it must reach `SUCCEEDED` before the question is committed. Record the date checked in the file header.
* **Wording:** different from the agent's `sample_questions` and from the measure `display_name`s for `synonym` questions; ask like a business user would.
* `split:` only to pin a question; otherwise `benchmark.assign_splits` decides from the id.

## 3. Coverage check (before any evaluation)

```
gos-benchmark coverage docs/tuning/benchmark ontology-metric-views/metric_views
# same as: python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage <questions_dir> <metric_views_dir> [--json]
```

Exit 0 is required. Exit 1 lists the problems (too few or too many questions, a view below `MIN_PER_VIEW`, an untagged measure or dimension, cross-view share below `MIN_CROSS_VIEW_SHARE`, an unused type, a missing `type:` tag or `expected_sql`, unknown names): add or fix questions, then re-run. Never evaluate on a set that fails coverage.

## 4. Evaluate

```python
from genie_ontology_modeled_knowledge_sdk import benchmark, geniespace
qs = benchmark.load_question_set("docs/tuning/benchmark")
splits = benchmark.assign_splits(qs)                 # HOLDOUT_SHARE by default
section = benchmark.to_space_benchmarks(qs)          # into build_space(..., benchmarks=section)
# render + deploy the agents bundle (approved sessions only), then:
run = benchmark.run_eval(space_id, ws)               # Genie benchmark evaluation run, both splits
summary = benchmark.score(run.results, splits)
entry = benchmark.history_entry(k, label, summary, eval_run_id=run.eval_run_id, changes=changes)
history = benchmark.append_history("docs/tuning/accuracy_history.json", entry)
benchmark.write_iteration_md(f"docs/tuning/iterations/{kk}.md", entry, state=benchmark.asymptote(history),
    results=run.results, plan_applied=plan_path, next_plan=next_plan_path)
```

* All questions, holdout included, are loaded into the agent's benchmarks (benchmarks do not feed answers), so one evaluation run scores both splits.
* **Fallback:** if the eval-runs API is refused or unavailable, use `benchmark.run_benchmark(space_id, qs, ws, warehouse_id=...)` (bounded concurrency, 429/5xx backoff) and say so in the iteration file. Pass `warehouse_id` so `expected_sql` is evaluated.
* Accuracy is `benchmark.score`'s definition; quote the "Scoring definition" section of the `benchmark.py` docstring in `iterations/00_baseline.md` instead of restating it. `unit_mismatch` and `needs_review` are misses; list them separately, they point to `format` or grading problems rather than semantics.

## 5. Triage tuning-split failures

Only failures in the tuning split. Classify each with exactly one category:

| Category | Symptom | Typical first ladder step |
|---|---|---|
| Missing measure | no measure computes what was asked; the agent improvises SQL or answers in text | 6 |
| Synonym gap | the agent picks the wrong measure or dimension, or cannot find the term | 2, 3 |
| Join issue | wrong totals (fan-out), missing rows, or the agent joins two views itself | 7 |
| Ambiguity | the term has two valid business meanings; the agent picks the other | 1, then 6 (split into two measures), 8 |
| Filter / edge | a business-rule `FILTER` is missing, or nulls / zero denominators are mishandled | 5 |
| Unit / format | `unit_mismatch` (ratio vs percentage) or wrong number format | 4 |
| Benchmark defect | the expectation itself is wrong | none: report `benchmark_defect`, do not tune for it |

## 6. The fix ladder

| Step | Layer | Change |
|---|---|---|
| 1 | metric view | `comment` on the measure, dimension or view |
| 2 | metric view | `synonyms` |
| 3 | metric view | `display_name` |
| 4 | metric view | `format` |
| 5 | metric view | measure/dimension expression or `FILTER` |
| 6 | metric view | new measure or dimension (right grain) |
| 7 | metric view | join fix per `verified_cardinality`, or move a measure to the right-grain view |
| 8 | glossary | glossary term file + draft UC Page |
| 9 | agent | one text instruction |
| 10 | agent | one example SQL, multi-step questions only |

Steps 9 and 10 need an **exhaustion record** for the failure, written in the tuning plan before the agent change:

```json
{"question_id": "sales_042", "category": "Ambiguity",
 "tried": [{"step": 1, "iteration": 1, "result": "still failing"},
           {"step": 6, "iteration": 2, "result": "still failing"},
           {"step": 8, "iteration": 2, "result": "not applicable: no glossary term"}]}
```

Every step 1-8 that applies is tried in an earlier iteration; a step that does not apply says why. No record, no agent change.

## 7. Tuning plans and the iteration loop

* The baseline (iteration 0) writes `docs/tuning/iterations/00_baseline.md`, the first history entry (`label: baseline`) and `docs/tuning/tuning_plan_01.md`.
* Iteration `k` applies `tuning_plan_<kk>.md`: mark each action `applied` or `reverted` with a one-line outcome, validate (`gos-validate-mv` on the metric views folder exits 0), re-register / redeploy what changed, re-evaluate, `append_history`, write `iterations/<kk>.md` (per split, per view, per type, delta, fixed / regressed / still failing tuning questions, `benchmark_defect` list), run `benchmark.asymptote`, and write `tuning_plan_<kk+1>.md` from fresh triage unless the rule is reached.
* A plan groups actions **by metric view**, each with ladder step, question ids, expected effect, status (`planned` / `applied` / `reverted`) and outcome (template in references).
* An action that broke previously passing questions is reverted in the next plan unless the net gain is positive and explained.
* At least `MIN_FIX_ITERATIONS` plans are applied in full, whatever the curve shows.

## 8. Stop rule

`benchmark.asymptote(history)` returns `{reached, reason, fix_iterations, last_deltas_pp, holdout_gap_pp, exhausted}`. It is reached when at least `MIN_FIX_ITERATIONS` plans were applied, the tuning-split accuracy gained less than `ASYMPTOTE_DELTA_PP` in each of the last `ASYMPTOTE_WINDOW` iterations (or is 100%), and the latest holdout accuracy is within `HOLDOUT_TOLERANCE_PP` of its best.

* **Conditional iterations** (after the required plans): first run `asymptote`. If `reached`, write `iterations/<kk>.md` with `converged at iteration <j>` and the `asymptote` output, change nothing else, and finish.
* If `exhausted` (not reached after `MAX_FIX_ITERATIONS` plans), say so plainly in `tuning_summary.md`; the owner decides whether to add iterations.
* A falling holdout while the tuning split rises is overfitting: revert the latest agent-layer changes first.

## 9. Summary

The last iteration writes `docs/tuning/tuning_summary.md` (template in references): accuracy curve for both splits, every change by ladder step and iteration, remaining failures with category and exhausted steps, and the count of instructions and example SQL with the reason each was needed.

## 10. Final evaluation: independent report simulation

After tuning, a **separate session** that never read `docs/tuning/**` or the agent's instructions, example SQL or benchmarks evaluates the agent the way report builders use it: personas, multi-turn conversations, ground truth pre-registered on the **source tables** (not the metric views). Method, rubric and outputs: [references/report-simulation.md](references/report-simulation.md). The tuning session does not run it.

## Output checklist

- [ ] `docs/tuning/benchmark/`: one file per view group plus `cross_view.yml`, tagged per the schema, every `expected_sql` ran `SUCCEEDED`; `gos-benchmark coverage` exits 0.
- [ ] Questions loaded into the agent's benchmarks; evaluation via `benchmark.run_eval` (or the recorded `run_benchmark` fallback); both splits scored.
- [ ] `accuracy_history.json` has the baseline and one entry per applied plan; `iterations/<kk>.md` per run.
- [ ] Only tuning-split failures triaged; holdout read as numbers only.
- [ ] Every agent change (steps 9-10) has an exhaustion record.
- [ ] At least `MIN_FIX_ITERATIONS` plans applied; tuning stopped by `benchmark.asymptote` (or `exhausted` stated).
- [ ] `tuning_summary.md` written.
