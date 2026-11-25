# Exhaustive Tuning Protocol

Design note for the Genie Ontology Modeled Knowledge SDK tuning stage (wave 8). The rules an agent follows are in [`skills/ontology-tuning`](../../skills/ontology-tuning/SKILL.md); the numbers and the stop rule are implemented in `genie_ontology_modeled_knowledge_sdk.benchmark`. This page explains why the protocol looks the way it does and how the run kit uses it.

## What changed from build-0

Build-0 tuned with 10-20 questions per agent, at most two fix iterations and a 70% accuracy gate. On TPC-H that produced a 93.3% baseline on 15 questions: a number too small to tell a real improvement from noise, and a set too small to touch every measure and dimension. The exhaustive protocol replaces it; the triage categories are kept.

## The numbers

All thresholds are constants in `benchmark.py`. Build-1 values:

| Constant | Value | Rule |
|---|---|---|
| `MIN_QUESTIONS`, `MAX_QUESTIONS` | 100, 498 | questions per agent (Genie allows `MAX_SPACE_BENCHMARKS` = 500 benchmarks per agent) |
| `MIN_PER_VIEW` | 12 | questions per metric view |
| `MIN_CROSS_VIEW_SHARE` | 0.25 | share of questions that need two or more metric views |
| `QUESTION_TYPES` | 8 types | `simple`, `breakdown`, `time`, `filter`, `ratio`, `synonym`, `edge`, `cross_view`; each used at least once |
| `HOLDOUT_SHARE` | 0.2 | deterministic holdout, `assign_splits` (hash of the question id) |
| `MIN_FIX_ITERATIONS` | 3 | tuning plans applied before the stop rule can fire |
| `ASYMPTOTE_DELTA_PP`, `ASYMPTOTE_WINDOW` | 1.0, 2 | tuning-split gain below 1.0 pp in each of the last 2 iterations (or 100%) |
| `HOLDOUT_TOLERANCE_PP` | 2.0 | latest holdout accuracy within 2.0 pp of its best |
| `MAX_FIX_ITERATIONS` | 6 | `asymptote` reports `exhausted` after 6 plans without reaching the rule |

Coverage is also structural: every measure and every dimension of every metric view is tagged by at least one question, and every question has tokenized `expected_sql` that ran `SUCCEEDED`. `benchmark coverage` checks all of it before any evaluation.

## Why a holdout

Tuning edits metric view comments, synonyms and, as a last resort, agent instructions, in response to specific failed questions. Every such edit risks fitting the wording of those questions rather than the business meaning. A 20% holdout that the tuning session never reads (it sees only the holdout accuracy, and `write_iteration_md` never lists holdout failures) measures whether a change generalizes. A tuning split that rises while the holdout falls is overfitting, and the latest agent-layer changes are reverted first. The split is a hash of the question id, so it is the same on every machine and every run, and the benchmark is frozen after the baseline so the curve compares like with like.

## Why the asymptote and not a fixed count

A fixed iteration count either stops while fixes are still paying off or keeps tuning after they stopped. The protocol instead requires a minimum of three applied plans (enough to see a trend and to give multi-step fixes room: a metric view change in one iteration, its effect checked in the next) and then stops when two consecutive iterations each gain less than one percentage point on the tuning split, with the holdout still near its best. `MAX_FIX_ITERATIONS` is a budget, not a target: reaching it without convergence is reported to the owner, who decides whether to continue.

## Why MV-first

A fix in a metric view (comment, synonyms, `display_name`, `format`, expression or `FILTER`, a new measure, a join fix) or in the glossary and UC Pages helps every consumer of the semantic layer: every Genie Agent, dashboard and Genie One user. A fix in one agent's instructions helps only that agent, is invisible to Unity Catalog, and is the classic way to overfit a benchmark. The fix ladder therefore orders the options:

| Steps | Layer |
|---|---|
| 1-7 | metric view: comment, synonyms, display_name, format, expression/FILTER, new measure or dimension, join or grain fix |
| 8 | glossary term + draft UC Page |
| 9 | one agent text instruction |
| 10 | one example SQL, multi-step questions only |

Steps 9-10 require an exhaustion record (`{question_id, category, tried: [{step, iteration, result}]}`) showing every applicable step 1-8 was tried in an earlier iteration. Instructions never restate metric view metadata.

## Evaluation

All questions, holdout included, are loaded into the agent's benchmarks (`to_space_benchmarks`), and one Genie benchmark evaluation run (`run_eval`, `/api/2.0/genie/spaces/{id}/eval-runs`) scores both splits. Benchmarks do not feed the agent's answers, so loading the holdout does not leak it. When the eval-runs API is unavailable, `run_benchmark` asks each question in its own conversation with bounded concurrency and 429/5xx backoff. Accuracy is `benchmark.score`'s definition; `unit_mismatch` (a ratio returned as a percentage) and `needs_review` count as misses and are reported separately.

## Final evaluation: report simulation

Benchmarks ask one question per conversation. Business users build reports: they drill down, compare periods and follow up on earlier answers. After tuning, an **independent** session that never reads the tuning files or the agent's instructions, example SQL and benchmarks plays 4-5 report personas, each in one Genie conversation of 8-15 turns written in advance, graded against ground truth pre-registered on the **source tables** (so a metric view defect cannot grade itself). Target 80% overall, recorded rather than gated. Method: [`skills/ontology-tuning/references/report-simulation.md`](../../skills/ontology-tuning/references/report-simulation.md).

## How the run kit uses it

| Run stage | Protocol step | Outputs |
|---|---|---|
| Benchmark authoring sessions (one per view group, plus cross-view) | author questions, run `expected_sql`, `benchmark coverage` exits 0 | `docs/tuning/benchmark/*.yml` |
| Baseline session (deploy) | load benchmarks into the agent, deploy, evaluate, triage, write plan 01 | `iterations/00_baseline.md`, `accuracy_history.json`, `tuning_plan_01.md` |
| Iteration sessions 1..`MIN_FIX_ITERATIONS` | apply plan, re-register / redeploy, evaluate, `append_history`, `asymptote`, next plan | `iterations/<kk>.md`, `tuning_plan_<kk+1>.md` |
| Conditional iteration sessions up to `MAX_FIX_ITERATIONS` | start with `asymptote`; if reached, record `converged at iteration <j>` and change nothing | `iterations/<kk>.md` |
| Last iteration | write the summary; its gate requires the asymptote | `tuning_summary.md` |
| Report simulation (independent) | personas, ground truth, conversations, grading | `docs/evaluation/**` |

Conditional iterations let the manifest declare the maximum number of waves up front while letting the build finish early: no manifest edits are needed when the curve flattens. In build-1 the TPC-H dogfood runs these stages as waves 1-6 (benchmarks), 1-7 (baseline), 1-8..1-10 (required plans), 1-11..1-13 (conditional) and 1-14 (report simulation); the run kit (`templates/run/`, build-1 session 28) is to carry the same stages for customer projects.
