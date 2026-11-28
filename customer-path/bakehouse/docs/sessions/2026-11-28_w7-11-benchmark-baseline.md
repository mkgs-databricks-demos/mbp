# 2026-11-28 — Wave 7, Session 11: Benchmark Baseline & Tuning Plan 01

* Build run: 409860738864401 (job 138308594859344, task `w7_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (checked read-only with `runGit status`; no Git commands that change state).
* Status: **pass**.

## Context

* Skills: the UC skill ids for `genie_build_session_runner` and `ontology-tuning` did not resolve through `readSkillFile`. I used the workspace fallbacks `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md` and `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-tuning/SKILL.md`.
* Read: `waves.json` (wave 7, session 11), plan 11, `PROJECT_MEMORY.md`, `sdk_config.json`, summaries for 09, 10a, 10b and 10c, the agent file, and `data_model_summary.md` (supplier join only). No `hi_genie/` folder.
* SDK wheel 0.1.1 (SDK checkout `dist/`) was installed in this session's serverless Python env only.

## What was done

1. **Splits.** `load_question_set` loaded 187 questions (a/b/x files). `assign_splits` gave 146 tuning and 41 holdout. `benchmark.coverage` reported 0 problems (31.6% cross-view, every type used). Wrote `docs/tuning/splits.json`.
2. **Benchmarks.** Added `to_space_benchmarks(qs)` (all 187 questions, holdout included) as `benchmarks` in `agents/bakehouse_retail_sales_agent.geniespace.json`, serialized with `geniespace.space_to_json`. `validate_space` returned no problems on the source and rendered files. `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` returned exit 0 (`target schema and 3 identifiers resolve`).
3. **Deploy.** `bundle validate --strict --target dev` passed. `bundle deploy --target dev` (owner-approved) updated `genie_spaces.bakehouse_retail_sales_agent`: 0 created, 1 changed, 0 deleted, deployment `3858229701455671` v2. Space `01f1eaeeac87195fa93d5b083cc91e84`: `update_time` 2026-11-28T06:19:46.993Z, 187 benchmark questions in the serialized space.
4. **Baseline.** `benchmark.run_eval` ran eval run `01f1eaf3c4a8155bbf2f167f93d93a39`, started 2026-11-28T06:20:12Z (after the build run started) and finished 06:55Z, with 187 results. Score: overall 150/187 (80.2%). Tuning split 117/146 (80.1%), holdout 33/41 (80.5%). 186 queries generated and succeeded, 0 errors, 0 `unit_mismatch`, 0 `needs_review`. Wrote `docs/tuning/accuracy_history.json` (iteration 0, `baseline`) and `docs/tuning/iterations/00_baseline.md` with `write_iteration_md` (it lists tuning failures only). `asymptote`: not reached (0 plans applied, 3 needed).
5. **Tuning plan 01.** Triaged the 29 tuning-split failures, grouped by metric view, with one category and one ladder step each:
   * Filter / edge: 6
   * Synonym gap: 7
   * Unit / format: 3
   * Ambiguity: 2
   * Join issue: 6
   * Benchmark defect: 5 (one is a candidate)

   No agent-layer actions are planned. Read-only value checks supported the triage: `ILIKE '%US%'` also matches Australia, `'%XL%'` also matches XXL, and `Customer State` mixes `CA` and `California`. Genie also used `Supplier Status` values that do not exist.

## Decisions / assumptions

* **All 187 questions in the benchmarks.** The manifest scope says "add the benchmarks", and plan task 2 says "tuning-split benchmarks". Task 4 (score both splits) and the tuning skill need the holdout loaded too, so I loaded all 187. Benchmarks do not feed answers.
* **Holdout blindness.** Holdout results were used as counts only. A programmatic check confirmed that no holdout id appears in `tuning_plan_01.md` or `00_baseline.md`.
* **Triage evidence limit.** The eval-run results carry the verdict and Genie's SQL but no result rows. Classification compares Genie SQL with `expected_sql`; value-level differences were not re-run per question.
* **SDK writes.** `splits.json`, the agent file, `accuracy_history.json`, `00_baseline.md` and `.rendered/` were written by SDK functions or Python in the session env, not by the editor tools, because of their size (187 SQL benchmarks). The plan file, this summary and the status file were written with the workspace file tools.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| benchmark coverage (187 questions) | pass (0 problems) |
| validate_space (source and rendered agent file) | pass |
| geniespace render `--check` | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle validate --strict --target dev` (ontology-metric-views, unchanged) | pass |
| `bundle deploy --target dev` (ontology-genie-agents) | pass |
| baseline_results (eval started 06:20:12Z, after build start; tuning and holdout recorded) | pass |
| tuning_plan_01 (29/29 tuning failures classified, 0 holdout ids cited) | pass |

## Requests / notes for later sessions

* Session 12 (tuning iteration 1): apply `docs/tuning/tuning_plan_01.md`, starting with the metric-view comments and value lists (S1, S2, C1, C2). C4 (supplier dimensions in `mv_bakehouse_sales`) is the largest change; it needs re-registration of the metric views.
* Owner: review the benchmark defects b-010, b-013, b-042, x-018 and x-056 (candidate). The benchmark is frozen, so they are not edited during tuning.

## Files

* `docs/tuning/splits.json` (new)
* `docs/tuning/accuracy_history.json` (new)
* `docs/tuning/iterations/00_baseline.md` (new)
* `docs/tuning/tuning_plan_01.md` (new)
* `ontology-genie-agents/agents/bakehouse_retail_sales_agent.geniespace.json` (benchmarks added)
* Gitignored `ontology-genie-agents/.rendered/` refreshed by the render step
