# Verdict warning when nothing was checked, generic docs, skill guidance (2026-11-08)

Branch `mg-genie-build-waves-verdict-disabled` (on top of 8122e2e).

## Problems

1. After 8122e2e, a run where every wave is disabled ended `BUILD_PASSED: 0 wave gate(s) passed (N disabled ...)`: a pass for a run that built and checked nothing.
2. Docs, skills, tests and code comments outside `docs/sessions/` named other projects (consumer project names, job/run/conversation IDs, a Genie space ID, a user path, app and space names). This repo is customer-facing.
3. The planner skill and the follow-up and repair prompts did not mention `continuation_passes`, disabled waves or the new warning, so a new project or session would not know about them.

## Changes

* `src/notebooks/gate_helpers.py`: `build_verdict` returns `warning: true` when nothing failed and no gate was checked. `verdict_message` then returns `BUILD_WARNING: no wave gate was checked in this run (<n> disabled: ...; <n> not in run ...)`. The run still succeeds (Jobs has no task-level warning state, and a failing non-leaf task to get `SUCCEEDED_WITH_FAILURES` would add a task for no benefit); the warning is in the task output, exit value and `build_verdict.json`.
* `src/notebooks/build_verdict.ipynb`: prints a `WARN:` line instead of the old `NOTE:`; markdown documents `BUILD_WARNING`.
* `tests/test_gate_helpers.py`: `test_verdict_warns_when_no_gate_was_checked` (all disabled with stale result files; disabled plus not-in-run; one checked gate is a normal pass; a failure is never a warning). Fails on the previous `gate_helpers.py` (KeyError `warning`).
* Generic references (no behaviour change): `docs/plans/2026-10-26_instance-state-isolation.md` (placeholders such as `Project A`, `<A-build>`; real values stay in its session summary), `docs/plans/2026-10-26_visible-failures.md`, `docs/plans/2026-10-26_request-probe-helpers-skill-doc.md`, `docs/design/runtime-target-extensions.md`, `gate_helpers.py` docstring, planner skill and `databricks.yml` suffix examples (`-my-project`), integrator skill example run ID, `tests/test_instance_guard.py`, `tests/test_session_status.py`, `tests/test_gate_helpers.py` fixtures.
* Skill and prompt guidance: planner skill (Step 6) explains `continuation_passes` (default 1, max 3, `0` off, 3 tasks per pass, 1000-task limit). `docs/prompts/follow-up-build.md` prefers `archived` over disabling tasks (setup resets the job) and mentions `BUILD_WARNING`. `docs/prompts/repair-failed-wave.md` explains Disabled waves and what to do on `BUILD_WARNING`. README describes the warning. Runner and integrator skills already covered continuation (d41a70e).

## Decisions

* Warning only when nothing was checked. A run with some disabled waves and at least one checked gate stays `BUILD_PASSED` and lists the skipped waves.
* `databricks.yml` still has the workspace host and the `prod` target's `root_path` / `run_as` user. That is deployment config, not a project reference; changing it would change where the bundle deploys. Left for a separate decision.
* Session summaries keep their specific IDs (they are the record the plans now point to).

## Verification

* pytest: 138 passed (136 + 1 from 8122e2e + 1 new).
* Grep outside `docs/sessions/` for project names, user names, real 12-19 digit IDs and Genie space IDs: only the `databricks.yml` deployment values remain; the remaining 16-digit values are the `1234567890123456` placeholders.
* `build_verdict.ipynb` is valid JSON with no outputs.

## Rollout

* `gate_helpers.py` and `build_verdict.ipynb` are read from the live Git folder: no redeploy or setup needed.
* Skill text: automations that read the workspace `SKILL.md` pick it up from the checked-out branch; UC-published skills need a setup rerun per instance.
