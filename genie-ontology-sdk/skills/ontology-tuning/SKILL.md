---
name: ontology-tuning
description: Benchmark deployed ontology Genie Agents (10-20 questions each), triage failures, and fix metric views before agent instructions in at most 2 iterations, writing docs/tuning/tuning_plan.md and benchmark_results.md. Load for the Genie Ontology SDK tuning stage or when asked to benchmark or tune ontology Genie Agents.
---

# Ontology Genie Agent Tuning

Measure how well the deployed Genie Agents of a Genie Ontology run answer business questions, then improve them with the smallest, most general fixes. Uses the SDK `benchmark` module. Templates: [references/templates.md](references/templates.md).

## The MV-first rule

**Fix the metric view first, the agent last.** A missing synonym, a vague comment, a missing measure or a wrong filter is fixed in the metric view YAML, where every agent, dashboard and Genie One user benefits. Change an agent's `.geniespace.json` only when a failure cannot be fixed in any metric view (a genuinely ambiguous term, a multi-step question the agent keeps getting wrong). Never add an instruction or example SQL that restates metric view metadata, and never add example SQL for a single-view, single-measure question: that is overfitting to the benchmark.

**Iteration limit: at most 2 fix iterations** after the baseline run (baseline -> fix 1 -> re-run -> fix 2 -> final run). Stop earlier when the gate passes. After iteration 2, stop and report what remains; do not keep tuning.

## Unattended-session rules

* No Git commands, no file deletion.
* Write only metric view YAML, `.geniespace.json` files and `docs/tuning/**` (or the paths your session owns).
* Re-register or redeploy only if your session is approved to deploy; otherwise list the needed redeploy as a request and benchmark what is deployed.
* Benchmark questions and expected SQL must not contain workspace-specific identifiers; use the `${target_catalog}.${target_schema}` tokens in committed files.

## 1. Inputs

| Input | Use it for |
|---|---|
| `docs/deployment/` (or the agents bundle `bundle summary`) | the deployed Genie space id of each agent |
| `docs/research/*.md` KPI definitions, `docs/semantics/*.md` | the questions and their business meaning |
| `ontology-metric-views/metric_views/**/*.yml` | current measures, synonyms, comments, filters |
| `ontology-genie-agents/agents/*.geniespace.json` | current sample questions, instructions, example SQL |

## 2. Generate benchmark questions (10-20 per agent)

Write `docs/tuning/benchmark_questions.yml` as a list of `{id, question, expected_sql?, expected_answer?, tags}` (one file; tag each question with its agent, e.g. `agent:<agent_name>`, or write one file per agent as `benchmark_questions_<agent>.yml` if the run kit says so).

Per agent, cover:

| Tag | Example shape |
|---|---|
| `simple` | single measure, no grouping ("Total revenue in 1995") |
| `breakdown` | measure by one or two dimensions |
| `time` | period comparison or trend |
| `filter` | a business filter (segment, region, status) |
| `ratio` | derived measure (average order value, margin %) |
| `synonym` | uses a research synonym instead of the measure name |
| `edge` | nulls, zero denominators, empty period |

* Use different wording from the agent's `sample_questions`; a benchmark that repeats them measures nothing.
* Add `expected_sql` (`MEASURE()` over the metric view, tokenized names) wherever the answer is derivable from one or two views; add `expected_answer` when you computed the value with a read-only query. Leave both out only when no expectation is derivable, and say why in the tags (`no_expectation`).
* Use `benchmark.load_questions(path)` to check the file parses before running.

## 3. Run the benchmark

```python
from genie_ontology_sdk import benchmark
questions = benchmark.load_questions("docs/tuning/benchmark_questions.yml")
agent_questions = ...  # the subset tagged agent:<agent_name>
results = benchmark.run_benchmark(space_id, agent_questions, ws, timeout_s=120)
summary = benchmark.score(results)
benchmark.write_results_md(summary, results, "docs/tuning/benchmark_results.md")
```

Run it per agent, with only that agent's questions. Keep the baseline results (copy the section into the iteration log of the results file before re-running).

**Accuracy** (as defined by `benchmark.score`; quote the `benchmark.py` docstring in the results file, and update this line if the docstring differs): `score` counts `sql_generated`, `sql_succeeded` and `matches_expected`, and **accuracy = matches_expected / questions with an expectation (`expected_sql` or `expected_answer`); if no question has an expectation, accuracy = sql_succeeded / total questions.**

**Gate:** accuracy >= 70% per agent.

## 4. Triage each failure

Classify every failed question with exactly one category, then pick the fix from the first column that applies:

| Category | Symptom | Metric view fix (do first) | Agent fix (only if the MV fix cannot work) |
|---|---|---|---|
| Missing measure | No measure computes what was asked; agent improvises SQL or answers in text | Add the measure (with `comment`) to the right-grain view | none |
| Synonym gap | Agent picks the wrong measure/dimension or says it cannot find the term | Add the user's term to `synonyms`; sharpen `display_name` | none |
| Join issue | Wrong totals (fan-out), missing rows, or the agent joins two views itself | Fix or remove the join per `verified_cardinality`; move the measure to the correct-grain view | `join_specs` entry between two views, only if verified |
| Ambiguity | Term has two valid business meanings; agent picks the other one | Clarify the measure `comment`; split into two named measures if both meanings are needed | One text instruction defining the term |

Also check filters (a measure missing a business-rule `FILTER`) and edge cases (null handling, zero denominators): those are metric view fixes too. An example SQL is allowed only for a multi-step question that still fails after the metric view fixes.

## 5. Fix and re-run (max 2 iterations)

For iteration `i` = 1, 2:

1. Apply the metric view fixes for all failures at once. Run `python -m genie_ontology_sdk.mv_yaml validate` on the metric views folder; it must exit 0.
2. Re-register the changed metric views (the metric-views bundle registration job) and, if `.geniespace.json` changed, redeploy the agents bundle, when your session is approved to; otherwise record the request and stop the loop.
3. Re-run the benchmark for the affected agents and re-score.
4. Log the iteration in `docs/tuning/tuning_plan.md`: failures, category, fix, file, and the before/after accuracy.
5. Stop if every agent is at or above the gate.

After iteration 2, stop. Record remaining failures with their category and a recommended next fix.

## 6. Write the outputs

Use the templates in [references/templates.md](references/templates.md):

* `docs/tuning/tuning_plan.md`: Phase 1 (metric view) actions, Phase 2 (agent) actions with the reason the MV fix was not enough, the iteration log, and remaining items.
* `docs/tuning/benchmark_results.md`: produced by `benchmark.write_results_md`, plus the quoted accuracy definition, baseline vs final accuracy per agent, and the iteration log.

## Output checklist

- [ ] `docs/tuning/benchmark_questions.yml` with 10-20 questions per agent, tagged, with `expected_sql` or `expected_answer` wherever derivable; `load_questions` parses it.
- [ ] Baseline and final runs via `benchmark.run_benchmark`, scored with `benchmark.score`.
- [ ] Every failure classified (missing measure / synonym gap / join issue / ambiguity) with its fix.
- [ ] Metric view fixes applied before any agent change; every agent change justified in Phase 2.
- [ ] At most 2 fix iterations; `mv_yaml validate` exits 0 after each.
- [ ] `docs/tuning/tuning_plan.md` and `docs/tuning/benchmark_results.md` written, with the accuracy definition quoted from `benchmark.py`.
- [ ] Accuracy >= 70% per agent, or the remaining gap and next fixes stated.
