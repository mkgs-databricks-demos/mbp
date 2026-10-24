# 2026-10-24 Jobs API 2.2 and archived waves

## Problem

A consumer manifest with 32 waves (22 from three finished builds, 10 for the next build) made the setup job fail in `reset_job_tasks()`:

`InvalidParameterValue: Resources with more than 100 tasks can only be handled by API 2.2 and above. Your resource has 128 tasks.`

## Root causes

1. Every Jobs call in the setup notebook used `/api/2.1`, which rejects jobs with more than 100 tasks. API 2.2 accepts them, but `jobs/get` and `runs/get` return at most 100 elements per array and a `next_page_token`; a `jobs/reset` built from a first-page read would silently drop job clusters, environments or parameters.
2. Setup generated tasks for every wave, including waves from finished builds that will never run again.
3. Found while verifying: dynamic value references only accept letters, digits and `_`, so `{{tasks.w4-0_gate.values.gate_passed}}` (wave id `4-0`) was rejected by `jobs/reset` as an unknown reference. Hyphenated task keys must be backtick-escaped.

## Changes

* New `src/notebooks/jobs_api.py`: `get_job` / `get_run` follow `next_page_token` (tasks, job_clusters, environments, parameters / job_parameters, iterations; repeated-token and page-count guards), `reset_job_tasks` builds `new_settings` from the fully paged read, plus `run_now`, `get_run_output`, `iter_genie_configuration_ids`. All on `/api/2.2`.
* New `src/notebooks/waves_manifest.py`: manifest validation and task generation moved out of the setup notebook so they can be unit tested. Adds wave-level `"archived": true` and an informational `build` label:
  * archived waves keep wave id / session id / mode / runtime target checks, skip rule 7 (single-writer) and the owned_paths warning;
  * no tasks for archived waves; the first runnable wave has no upstream dependency;
  * `depends_on` naming archived sessions is satisfied (`unmet_dependencies`); new warnings for unknown or same/later-wave dependencies;
  * wave ids must be valid task-key prefixes; all-archived manifests are rejected;
  * `ref_ident()` backtick-escapes non-plain task keys in the gate_check condition (plain ids such as `0`, `4a` are unchanged);
  * summary line `Manifest OK: N waves (A archived, R runnable), S sessions, T runtime targets`.
* `setup_build_waves_job`: imports both modules; no `/api/2.1` left; after `jobs/reset` it reads the job back (all pages) and fails if the task keys differ; automation reuse scans every page of tasks.
* `wave_gate_check`: matches the wave id as a string, refuses archived waves, unclaimed-carryover rule uses the last runnable wave. Its SDK calls (`jobs.list`, `list_runs`, `get_run().start_time`) read no task arrays.
* Runner skill: archived wave = error; archived dependencies satisfied, never look for their status files. Integrator skill: first/last/later wave mean runnable waves; never expect status files for archived sessions.
* Docs: README (archived waves section, architecture rows, changing a build), `docs/manifest-schema.md` (fields, design rule 10, Archived waves section), planner skill, follow-up prompt.
* Tests (`tests/`, 32): fake 2.2 Jobs service (100-element pages, 2.1 rejection) for paged job/run reads and a reset of a 128-task job; archived + runnable waves; backwards compatibility with all three examples.

## Verification

* `pytest tests`: 32 passed.
* `bundle validate --strict --target dev`: OK.
* Setup job against the 32-wave manifest: SUCCESS, printed `Manifest OK: 32 waves (22 archived, 10 runnable), 63 sessions, 19 runtime targets`, build job reset to 40 tasks (all `w4-*`, first task without dependencies, escaped gate_check references), all four automations updated (none created). The first attempt failed on the unescaped reference (cause 3), before the job was changed.
* Not exercised live: a `jobs/reset` with more than 100 tasks (covered by the fake-client test).

## Deployment notes

* No `bundle deploy` needed: nothing under `resources/` changed. Jobs run the notebooks and read `src/skills` from the live mbp Git folder (source WORKSPACE), so the change is live as soon as the folder is on the right commit.
* Skills are already republished. Every dev instance (default, `-sgt-root`, `-agentic-trading`) publishes to the same UC skills schema, `hls_fde_dev.dev_matthew_giglia_build_waves`, so the one setup run above updated the runner and integrator skills for all of them. This is safe: the new rules only apply to manifests with `"archived": true`.
* Other instances keep their old task graph until their own setup job runs. Rerun setup for an instance before using it with an archived-wave manifest.
* The mbp Git folder stays on `mg-genie-build-waves-api22-archived` until the PR is merged, then switches back to `main`. No republish is needed after the switch, because the merged files are identical.

## Decisions

* Archived waves are validated, not ignored, so `depends_on` and runtime targets that point at old sessions still fail loudly when wrong.
* Validation and task generation live in plain modules (`waves_manifest.py`, `jobs_api.py`) so they can be unit tested without a cluster.
* After a reset, setup reads the job back and compares task keys. A paging bug would then fail the run instead of silently dropping tasks.

## Files

`src/notebooks/jobs_api.py`, `src/notebooks/waves_manifest.py`, `src/notebooks/setup_build_waves_job.ipynb`, `src/notebooks/wave_gate_check.ipynb`, `src/skills/genie-build-session-runner/SKILL.md`, `src/skills/genie-build-wave-integrator/SKILL.md`, `src/skills/genie-build-planner/SKILL.md`, `README.md`, `docs/manifest-schema.md`, `docs/prompts/follow-up-build.md`, `tests/conftest.py`, `tests/test_jobs_api.py`, `tests/test_waves_manifest.py`.
