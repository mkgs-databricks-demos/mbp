# 2026-11-27 — Wave 5, Session 09: Genie Agent Deployment & Probe

* Build run: 244030216249267 (job 138308594859344, task `w5_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute` + `allow_deploy`. Workflow `hybrid`, branch `genie-build-bakehouse` (read-only `git rev-parse`; no state-changing Git commands).
* Status: **blocked** (deploy stopped before any change; it needs to delete a Genie space this session did not create).

## What was done

1. Skill: the UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` did not resolve through `readSkillFile`; used the workspace fallback `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md`.
2. Context read: `waves.json` (wave 5, session 09), plan `plans/09_agent_deployment.md`, `PROJECT_MEMORY.md`, `sdk_config.json`, session 08 summaries and status, `ontology-genie-agents/README.md`, `databricks.yml`, `resources/genie_agents.yml`, `docs/registration/resolved_target.json`. No `hi_genie/` folder at the build root. The dev `variable-overrides.json` exists (not read or printed).
3. Installed SDK wheel 0.1.1 (SDK checkout `dist/`) into this session's serverless Python env only.
4. Task 1 render: `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check`, run in-process (`runpy`, as session 08 did because the shell subprocess fails auth) -> `check: target schema and 3 identifiers resolve`, exit 0, rendered `.rendered/bakehouse_retail_sales_agent.geniespace.json` (gitignored).
5. `bundle validate --strict --target dev` (ontology-genie-agents): `Validation OK!`.
6. `bundle deploy --target dev`: **refused by the CLI** without `--auto-approve`:
   > This action will result in the deletion or recreation of the following Genie spaces. The conversation history attached to a deleted space is permanently lost: delete resources.genie_spaces.tpch_supply_chain_agent ... Error: the deployment requires destructive actions, but the current console does not support prompting.
   Nothing was uploaded or changed (`Files: 0 uploaded, 0 deleted`).
7. `bundle summary --target dev` (read-only) confirms the cause: the dev state at `/Workspace/Users/matthew.giglia@databricks.com/.bundle/ontology-genie-agents/dev` already tracks `tpch_supply_chain_agent` (space `01f1e8a428241105b01bbc2f4e355e30`, `modified_status: deleted`), and `bakehouse_retail_sales_agent` is `modified_status: created` (not yet deployed).

## Root cause

The bakehouse Genie Agents bundle has the same bundle name (`ontology-genie-agents`) and dev target as another Genie Ontology project (TPC-H supply chain), so both share one deployment root and state. Deploying bakehouse would delete the TPC-H project's agent. Deleting what this session did not create is not approved, and `--auto-approve` would be a workaround, so the session stopped. Tasks 2-4 (space ids, probes, `docs/deployment/deployment_results.md`) were not run.

## Owner decision needed (one of)

* Give this project's bundle a unique name or root path (for example `bundle.name: ontology-genie-agents-bakehouse`, or a project-specific `workspace.root_path`) so it gets its own state; then re-run this session. This is a file change outside session 09's `owned_paths` (`ontology-genie-agents/databricks.yml`), so it needs the owner or a planned session. Recommended: the TPC-H agent stays untouched.
* Or approve deleting space `01f1e8a428241105b01bbc2f4e355e30` (`tpch_supply_chain_agent`) and deploying with `--auto-approve`.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| geniespace render `--check` (resolved_target.json) | pass |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |
| `bundle deploy --target dev` | fail (blocked: destructive delete of another project's space) |
| agent_probe | skipped (not deployed) |

## Files

* None changed (only this summary and `.build-status/244030216249267/09.json`). Gitignored `ontology-genie-agents/.rendered/` refreshed by the plan-mandated render step.
