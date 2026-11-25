# Build-1 planning

Date: 2026-11-25 | Branch: `mg-genie-ontology-build-1-plan` (from `mg-genie-ontology-build-1-dev-domain` at `5a4882f`, which contains `main` `92c38ff`)

## Problem
Plan build 1 from the owner-accepted requests R1-R9 and the 31 build-0 observations, plus an owner addition: exhaustive tuning (at least three tuning plans, 100-498 benchmark questions covering every metric view and cross-view questions, MV-first with instructions/example SQL only after all Unity Catalog semantic options are exhausted, tune until the asymptote) and an independent report-perspective simulation as the final evaluation.

## Findings before planning
* `mg-genie-ontology-build-1-dev-domain` (dev Pages domain decision) is **not merged**: one commit ahead of `main`, still on the remote. The build-1 branch was created from its tip so the decision is included; merging either PR first causes no conflict.
* Genie allows 500 benchmark questions per agent and exposes benchmark evaluation runs (`/api/2.0/genie/spaces/{space_id}/eval-runs`, results paged at 100). That makes 100-498-question evaluations server-side, so a tuning session does not spend its time limit asking questions one by one.
* genie-build-waves rules applied: archived build-0 waves, top-level `branch`, `authorization_policy`, explicit `bundle.deploy` naming each subfolder bundle (tier 1 covers only `bundle:build_root`), `jobs.run_now` for registration, `owned_assets` text equal to authorization targets, `manual_prereqs` for owner steps, one session per deploying wave.
* The 5 build-0 entries in `docs/plans/authorizations.monitor.json` belong to archived sessions; setup drops them (checked with `filter_monitor_grants`: 0 kept, 5 dropped). Left as history.

## Decisions
* **Owner (2026-11-25):** Devin runs build 1 as the level-4 external monitor, **as autonomous as possible**. Applied: explicit owner authorizations for every side effect; `monitor_may_authorize` covers `jobs.run_now`, `bundle.deploy`, `volume.write`, `workspace.write`, `sql.ddl`, `uc_skills.publish` on `owned_assets`; accuracy targets recorded rather than gated where a miss is not a defect; conditional tuning waves 1-11..1-13 pass with "converged" instead of needing manifest edits; owner prerequisites grouped so P1-1..P1-5 can all be done before the run starts.
* **Defaults applied (owner did not object to the proposals):**
  * repo-root files (GitHub workflows, `skills.yaml`) are staged under `ci/` and moved by the owner in the PR;
  * stop rule: after >= 3 applied tuning plans, < 1.0 percentage point gain in each of the last 2 iterations (or 100%), holdout within 2.0 points of its best; iterations 4-6 conditional; wave 1-13 fails if not reached by iteration 6;
  * report simulation: 80% target, recorded (backlog item below target), not gated.
* Workspace-specific values for build 1 go in a gitignored `.local/build-1.json` (`skills_catalog`, `skills_schema`, `scratch_schema`, `pages_domain_id`, later `customer_path_root`); `.local/` added to `.gitignore`.
* R9 is split around an owner-run (or Devin, with hand-off approval) child build: session 43 prepares, P1-6 runs the child build, session 44 reports. Sessions cannot create Git folders or deploy instances.
* `examples/tpch/docs/registration/resolved_target.json` is the one committed file allowed to hold a resolved dev schema name (it is the single source of truth R4 asks for).

## Result
18 waves `1-0`..`1-17`, 28 sessions `18`-`45` ([wave map](../plans/build-1/INDEX.md#wave-map)). Every R1-R9 request and every build-0 observation is mapped to a session or listed as "no change" in the INDEX.

## Owner prerequisites (not run; ask before any of them)
| Id | When | Step |
|---|---|---|
| P1-1 | before 1-0 | Vars file `~/genie-build-waves-instances/genie-ontology-sdk.vars.json`: `build_root` and `manifest_path` to `mbp/genie-ontology-modeled-knowledge-sdk`; redeploy with `scripts/deploy_instance.py` (web terminal); run setup |
| P1-2 | before 1-0 | `.local/build-1.json` with the four keys; create the scratch schema |
| P1-3 | before 1-3 | Skills previews on; skills schema created; build identity granted USE CATALOG, USE SCHEMA, CREATE VOLUME, READ VOLUME, WRITE VOLUME |
| P1-4 | before 1-5 | `consumer_group` in both TPC-H `variable-overrides.json` |
| P1-5 | before 1-5 | Delete `examples/tpch/ontology-genie-agents/agents/ontology_agent.geniespace.json` |
| P1-6 | before 1-16 | Child build on the second domain per `docs/customer-path/run_plan.md` |
| P1-7 | after merge | GitHub OIDC service principals, `production` environment, branch protection; move `ci/` files to the repo root |

The development Pages domain for `pages_domain_id` is the one chosen in [2026-11-25_build-1-dev-pages-domain.md](2026-11-25_build-1-dev-pages-domain.md).

## Verification
* `validate_manifest`: 0 errors, 0 warnings; `Manifest OK: 29 waves (11 archived, 18 runnable), 47 sessions, 0 runtime targets, continuation passes: 1 per wave, 163 job tasks`.
* `validate_authorizations`: 0 errors, 0 warnings; `plan_deploy_warnings` over the plan files: none; every authorization target is in its session's `owned_assets`.
* Every `plan_file` of runnable sessions and prerequisites exists.
* SDK tests from a `/tmp` copy with `GENIE_BUILD_WAVES_DIR` set: 280 passed, none skipped.
* Not verified: the Genie benchmark section field names in `.geniespace.json` (session 19 must read them from an exported space), whether Genie Code job tasks may call eval-runs and Pages writes (sessions 31/35 have fallbacks), and that unattended tasks load Unity Catalog skills (session 27's spike).

## Addendum: SDK wheel distribution (R7a)

**Request (owner, same day):** add SDK wheel distribution after R7 and fold it into the wave map. **Decision: ship both** (wheel by default, vendoring opt-in for no package egress or locked-down workspaces).

**Verified before planning:** `pyproject.toml` (setuptools, `src/` layout, `schemas/*.json` package data, version 0.0.1, `databricks-sdk>=0.40`); no bundle at the SDK root; `VENDORED_MODULES` = `mv_yaml`, `manifest`, `geniespace`; the template notebooks import only `mv_yaml` and `manifest` (`manifest` imports `mv_yaml`), so the vendored set is enough today but must follow the import closure once build-1 adds modules; `load_sdk()` registers the vendored folder, else imports the installed package; the template job has no `environments`; the init notebook edits `sys.path`; the vendored-copy and loader tests exist. No test depends on `examples/tpch`'s vendored copy, so the owner can delete it before the build.

**Docs checked (2026-11-25):** `artifacts.<name>: {type: whl, path, build}` builds on deploy; a `/Volumes/...` `workspace.artifact_path` makes the CLI upload referenced artifacts to the volume (no DBFS); serverless notebook tasks default to the notebook environment and accept a job-level environment with `/Volumes/...whl` dependencies (`environment_key`); classic compute uses `libraries: [{whl}]`; pure-Python wheels only. Not settled by the docs, so session 23b verifies on the platform: the upload sub-path under `artifact_path`, whether an unreferenced artifact is uploaded (the plan adds an `sdk_smoke` job that references it), and dynamic versioning.

**Changes:**
* `REQUESTS.md`: new **R7a** after R7 (current state, platform facts, 8 changes, acceptance criteria, dependencies, owner prerequisites); R2 scope note (R7a carries its distribution items, R2 keeps entry points); R9 depends on R7a and uses the wheel; sequencing step 3b.
* Manifest: session 23 rescoped (R2 + R7a code, SDK-root bundle, wheel-first templates, `vendor=False` default) with gate checks `sdk_bundle_validate`, `installed_wheel_tests`, `vendor_modes`; new single-session deploy wave **1-2b** (session **23b**: deploy the SDK bundle, run `sdk_smoke`, verify exactly one 0.1.0 wheel, record the stable path) with prerequisite **P1-8** and explicit `bundle.deploy` / `jobs.run_now` / `volume.write` approvals; session 27 depends on 23b; session 30 drops its own wheel upload, proves identical DDL before and after the move (`ddl_identical`) and only then applies observation 30; P1-4 adds `sdk_volume_path`; P1-5 also deletes the TPC-H vendored folder; sessions 28/29 scopes cover `sdk_version`, the volume prerequisite, the `vendor` widget and "Getting the SDK" in `docs/usage.md`.
* Plans: 23 rewritten, 23b new; 27, 28, 29, 30, 43 updated; INDEX (wave map, contracts, owned paths, prerequisites, plan list).
* PROJECT_MEMORY: build-1 decision "ship both, wheel by default".

**P1-8 (owner, not run):** create the SDK wheel UC volume (or approve it as a bundle resource); grant `WRITE VOLUME` to the build identity and the CI publishing service principal and `READ VOLUME` to project job run-as principals and the genie-build-waves run-as user; write `sdk_volume_path` in the SDK bundle's gitignored dev overrides.

**Verification (addendum):** `validate_manifest` and `validate_authorizations` 0 errors, 0 warnings; 30 waves (11 archived, 19 runnable), 48 sessions, 172 job tasks; `plan_deploy_warnings` none; every authorization target is in its session's `owned_assets`; every plan file exists; relative links resolve; no workspace ids or user paths outside `docs/sessions/`; SDK tests from a `/tmp` copy: 280 passed.

## Files modified
* `docs/plans/waves.json` (build-0 waves archived; build-1 waves, branch, policy, context files)
* `docs/plans/build-1/INDEX.md` and 23 plan files (`18_*`..`45_*`, `36-41_tuning_iteration.md`)
* `docs/plans/INDEX.md` (pointer to build 1), `.gitignore` (`.local/`)
* `PROJECT_MEMORY.md`, this summary, `docs/sessions/INDEX.md`
* Addendum: `docs/plans/build-1/REQUESTS.md`, `docs/plans/build-1/23b_wheel_publish.md` (new), plans 23, 27, 28, 29, 30, 43
