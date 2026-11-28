# 2026-11-28 — Wave 5, Session 09: Genie Agent Deployment & Probe

* Build run: 409860738864401 (job 138308594859344, task `w5_session`), continuation 0, first attempt for this run.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` at `6169665`, read-only `git rev-parse` / `status`; no state-changing Git commands).
* Status: **pass**.

## Context

* Previous run 244030216249267 was blocked: the bundle name `ontology-genie-agents` shared deployment state with another project, and deploy would have deleted that project's Genie space. Commit `02ab257` (owner) renamed the bundle to `bakehouse-ontology-genie-agents`, so it now has its own state at `~/.bundle/bakehouse-ontology-genie-agents/dev`. That resolves the earlier request.
* Skill: the UC skill id for the session runner did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
* Read: `waves.json` (wave 5, session 09), plan 09, `PROJECT_MEMORY.md`, session 08 summary for this run, previous session 09 summary/status, bundle README, `databricks.yml`, `resources/genie_agents.yml`, agent file, `resolved_target.json`. No `hi_genie/` folder at the build root. The dev `variable-overrides.json` exists (not read or printed).

## What was done

1. Installed SDK wheel 0.1.1 (SDK checkout `dist/`) into the session's serverless Python env only.
2. Render (in-process `runpy`): `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` -> `check: target schema and 3 identifiers resolve`, exit 0 (gitignored `.rendered/` refreshed).
3. `bundle validate --strict --target dev`: Validation OK.
4. `bundle deploy --target dev` (owner-approved): `Created genie_spaces.bakehouse_retail_sales_agent`; 1 created, 0 changed, 0 deleted. Deployment id `3858229701455671` v1.
5. `bundle summary`: space id `01f1eaeeac87195fa93d5b083cc91e84`, title `[dev matthew_giglia] Bakehouse Retail Sales Agent`, warehouse `24087b85239cacac`. Space `create_time`/`update_time` 2026-11-28T05:43:44Z, after build run start 05:05:18Z.
6. Probe: "Which 5 franchises had the highest gross sales?" -> message `COMPLETED`, query attachment, result `SUCCEEDED`, 5 rows (Baked Bliss 6642 top, matching session 08's example SQL run).
7. Wrote `docs/deployment/deployment_results.md`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| geniespace render `--check` | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle deploy --target dev` | pass |
| deployed after build run start | pass |
| agent_probe | pass (1/1 SUCCEEDED query attachment) |

## Notes for later sessions

* Session 10 (benchmarks/tuning): the agent is space `01f1eaeeac87195fa93d5b083cc91e84`. The earlier space from the shared-state deployment (if any) is not tracked by this bundle; nothing was deleted.
* Genie also returned a follow-up suggestion text attachment alongside the answer; no impact on the probe.

## Files

* `docs/deployment/deployment_results.md` (new). Gitignored `ontology-genie-agents/.rendered/` refreshed by the plan-mandated render step.
