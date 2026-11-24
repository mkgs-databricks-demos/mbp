# 2026-11-24 — Build-Waves Instance Deploy & Monitor Hand-off Prep

## Goal
Verify the owner's first deploy of the genie-build-waves instance for build-0, record it, and prepare Devin to execute and monitor build-0 at level 4.

## Deploy (owner, web terminal)
`scripts/deploy_instance.py --target dev --vars ~/genie-build-waves-instances/genie-ontology-sdk.vars.json` (check-only, then deploy). Output: no local cache to move, no remote state (first deploy), pre-deploy checks passed, 5 resources created, post-deploy checks passed, cache cleared.

## Verification (my read-only checks, Jobs API)
| Job | Id | Name | Notes |
|---|---|---|---|
| build_waves | `419885870201924` | `[dev matthew_giglia] Genie Ontology SDK: Build Waves` | params `branch` = `mg-genie-ontology-modeled-knowledge-sdk`, `build_root` = `/Workspace/Users/matthew.giglia@databricks.com/mbp/genie-ontology-sdk`, `manifest_path` = `.../docs/plans/waves.json`; tasks = `placeholder` (setup not run); run_as owner; tags managed_by=genie-build-waves |
| setup_build_waves | `408923363752593` | `... Build Waves Setup` | notebook `mbp/genie-build-waves/src/notebooks/setup_build_waves_job`; params `run_smoke`, `force` |
| build_waves_smoke | `280812597496325` | `... Build Waves Smoke Test` | |

All three have `deployment.metadata_file_path` = `/Workspace/Users/matthew.giglia@databricks.com/.bundle/genie-build-waves-genie-ontology-sdk/dev/state/metadata.json` (this instance's root, no takeover of other instances).

## Monitor prerequisites (README "External monitor", monitor SKILL.md)
* Monitor principal: `mkgs-devin` (application id `72bab3e9-303d-4443-b43e-9eaab474d8bb`, SCIM id `73590767487896`, active).
* Vars file updated (outside the repo): `monitor_principal` = that application id, `monitor_job_level` = `CAN_MANAGE_RUN`. **Needs a redeploy** (web terminal) to put the grant on the build and setup jobs; the first deploy had no monitor entry.
* `build_root` folder (`975815647682062`) ACL: owner + admins only (inherited). Monitor needs `CAN_READ` (owner confirmation).
* Setup must run **after** the redeploy (a deploy resets the build job to the placeholder task). Setup publishes `genie_build_monitor` to `hls_fde_dev.dev_matthew_giglia_build_waves` and grants the monitor USE CATALOG / USE SCHEMA / READ VOLUME on that skill. The same schema serves the other instances, so setup republishes their runner/integrator skills too.
* Devin egress IP may change per session; the workspace IP access list may need its address.

## Decisions
* Owner: Devin executes and monitors build-0 at level 4 and may decide on its own to progress the build to completion (within the monitor skill's guardrails and stop conditions).

## Setup, Devin hand-off and first run
* Owner redeployed with the monitor variables: `mkgs-devin` has `CAN_MANAGE_RUN` on the build and setup jobs (verified). Owner decided the monitor does not need `CAN_READ` on `build_root` (code reaches it through Git).
* Setup run `662686225923382`: SUCCESS, build job patched to 100 tasks, smoke 3, skills republished, `monitor_grants` null.
* Devin session `devin-fa7d5d07a8be443bbb29c02f9477a838` (level 4, `max_repairs` 8). It pushes with its direct GitHub token (Devin git proxy returns 403).
* Gap found by Devin: setup reset the build job's `branch` default to empty because `waves.json` had no top-level `branch`; Devin passed `branch` explicitly (`PARAMETER_OVERRIDE` warning).
* Build run `701596191246320`: waves 0-0..0-5 PASS (commits `9393658e854a`, `de59499a21fb`, `fd4918d177dd`, `fefa27e81117`, `844330748113`, `c5aec15e6a89`), no continuations. Wave 0-6 FAIL: session 12 deployed the metric-views bundle but `bundle run register_metric_views` was refused (only `bundle.deploy` was authorized; `allow_deploy` without `runtime_targets` implies no `jobs.run_now`). Checks `registration_job` and `mv_smoke` failed; waves 0-7..0-10 excluded. Devin escalated (0 repairs used).
* **Root cause:** my build-0 plan gave sessions 12/16 no `jobs.run_now` approval.
* **Decision (owner): option 2** — let the monitor grant run approvals itself. `waves.json` now has top-level `branch` and `authorization_policy.monitor_may_authorize` = `jobs.run_now` and `bundle.deploy`, both scope `owned_assets` (exact `owned_assets` text of the session). Verified: `validate_manifest` and `validate_authorizations` 0 errors / 0 warnings; `filter_monitor_grants` keeps run grants for 12 and 16 with exact owned_assets text and drops other targets and owner-only actions.

## Files modified
* `docs/plans/waves.json` (branch, authorization_policy)
* `PROJECT_MEMORY.md` (status, executor, next steps, monitor decision)
* this summary, `docs/sessions/INDEX.md`
* outside the repo: `~/genie-build-waves-instances/genie-ontology-sdk.vars.json`
