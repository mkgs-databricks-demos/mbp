# 2026-11-27 — Wave 4, Session 08: Genie Agent Curation (re-validation)

* Build run: 244030216249267 (job 138308594859344, task `w4_session`), continuation 0, first attempt for this run.
* Mode: `edit` + `allow_execute` (no deploy). Workflow `hybrid`, branch `genie-build-bakehouse` (read-only `git rev-parse`; no state-changing Git commands).
* Status: **pass** (already completed in build run 38498872047824; outputs regenerated in scratch and found identical, no files changed).

## Context

Session 08 passed in build run 38498872047824 (`2026-11-27_w4-08-agent-curation.md`). In this run, wave 1 session 02 renamed the glossary terms Customer and Supplier to Bakehouse Customer and Bakehouse Supplier; session 05 re-validated the metric view YAML with no changes; session 06 redeployed and re-registered the same 3 views (run 377694921681813, SUCCESS, 3/3 registered).

## What was done

1. Skills: the UC skill ids for the session runner and `ontology-agent-curation` did not resolve through `readSkillFile`; used the workspace fallbacks (`mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`, `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-agent-curation/SKILL.md`).
2. Read `waves.json`, plan 08, `PROJECT_MEMORY.md`, `sdk_config.json`, this run's session 02/05/06 summaries, the earlier session 08 summary and status, `registration_results.md`, `manifest.json` and the current owned files. No `hi_genie/` folder at the build root.
3. Impact of the rename: the agent file, resource entry and domain manifest do not use glossary term names (only generic words in instructions and questions, and view names). No change needed.
4. Installed SDK wheel 0.1.1 (SDK checkout `dist/`) into the session's serverless Python env only.
5. Regenerated in scratch: `plan_agents` over the 3 registered views with `max_per_agent=30` -> 1 agent `bakehouse_retail_sales_agent`. `build_space` with the same questions, instructions and example SQL gave text byte-identical to the committed file (`space_to_json` == file). `write_domain_manifest` with the same descriptions gave text identical to `docs/domain_manifest.yml`. Nothing was rewritten.
6. Ran the README render step in-process: `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` -> `check: target schema and 3 identifiers resolve`, exit 0 (refreshed gitignored `.rendered/` output).
7. Ran `EXPLAIN` and the query for both example SQLs on the resolved dev schema: both pass (latest week 2024-05-13: 17715 vs 28509, -37.9%; top franchise Baked Bliss 6642), same as the earlier run.
8. `bundle validate --strict --target dev` for `ontology-genie-agents`: `Validation OK!`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| agent count rule (3 views <= 30 -> 1 agent, `plan_agents`) | pass |
| `validate_space` on committed file and rebuilt doc | pass (0 errors) |
| rebuilt agent file byte-identical to committed | pass |
| rebuilt domain manifest identical to committed | pass |
| no literal catalog/schema/warehouse id (`hls_fde`, `dev_matthew_giglia`, warehouse id, `samples.`) in agent file or resources | pass |
| referenced views registered (`registration_results.md`, this run) | pass (3/3) |
| render `--check` with `resolved_target.json` | pass |
| example SQL `EXPLAIN` + run | pass (2/2) |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |

## Files

* None changed (only this summary and `.build-status/244030216249267/08.json`). Gitignored render output `ontology-genie-agents/.rendered/` refreshed by the plan-mandated render step.

## Requests / notes

* None new. Owner decisions carried from session 05 (supplier coverage basis, approved supplier share basis) remain open; the second text instruction can go once encoded in the view.
