# Build-1 owner prerequisites, instance retarget and Devin hand-off

Date: 2026-11-25 | Branch: `mg-genie-ontology-build-1-plan` | Follows [Build-1 planning](2026-11-25_build-1-planning.md)

The Genie Code session that took the build-1 plan to a running build: plan changes (R7a SDK wheel distribution, one SDK schema), the owner prerequisites, the genie-build-waves instance retarget, and the Devin hand-off.

## Problems
1. The plan needed SDK wheel distribution (owner: ship both, wheel by default, vendoring opt-in) and fewer schemas (the first prerequisite draft proposed three).
2. The owner prerequisites (P1-1..P1-8) had to be done before Devin could run build 1 without stopping.
3. The genie-build-waves instance still pointed at the pre-rename folder `mbp/genie-ontology-sdk`.

## Plan changes (committed)
* `f560977`: request **R7a** (SDK wheel distribution) after R7; session 23 rescoped; new single-session deploy wave **1-2b** (session **23b**, wheel publish); session 30 proves identical DDL before the observation-30 change.
* `159fd76`: **one SDK schema** chosen in SDK setup (catalog and schema asked, new schema recommended), deployed as a bundle with a schema resource; session 18 bootstraps and deploys it in wave 1-0; skills, the `sdk_wheels` volume and `scratch_*` views live in it; `notebooks/setup_sdk` added to session 29.
* `d3fcb9d`: hand-off decisions in `PROJECT_MEMORY.md`.
* Manifest after the changes: `validate_manifest` and `validate_authorizations` 0 errors, 0 warnings; 30 waves (11 archived, 19 runnable), 48 sessions, 172 job tasks; 280 SDK tests pass.

## Owner prerequisites

| Id | What was done | Evidence |
|---|---|---|
| P1-1 | Vars file (outside the repo) retargeted: `build_root`, `manifest_path` to the renamed folder, `build_branch` = `mg-genie-ontology-build-1-plan`. Owner deployed with `scripts/deploy_instance.py --force` (the instance guard flagged the changed `manifest_path` and the last build-0 run's old manifest; job ids in the summary and the remote state matched, so the change was intended). Setup needed `force=true` for the same reason | Deploy: 3 jobs updated, ids unchanged (build `419885870201924`, setup `408923363752593`, smoke `280812597496325`). Setup run `511569926811298` SUCCESS: branch synced (manifest source, `159fd76`), 172 build tasks patched, monitor skills republished, 5 build-0 grants dropped (archived sessions), `mkgs-devin` keeps `CAN_MANAGE_RUN` on build and setup jobs. Smoke run `110127788844049` SUCCESS (2/2 sessions, capability probe; app probe skipped, no app targets) |
| P1-2 | `.local/build-1.json` with `pages_domain_id` (development domain) | parses, gitignored, untracked |
| P1-3 | Skills preview confirmed by the owner | owner |
| P1-4 | TPC-H overrides: `consumer_group` = `admins` in both, `sdk_volume_path` (the predicted dev path of the SDK `sdk_wheels` volume) in the metric-views one | both bundles `bundle validate --strict -t dev` OK; agents `schema` holds the 7 metric views |
| P1-5 | Deleted the placeholder agent file and the TPC-H vendored SDK folder (`4c678b7`) | not in `git ls-files`; 280 tests pass |
| P1-8 | SDK bundle overrides at `build_root`: `sdk_catalog`, `sdk_schema` = `ontology_sdk`, `sdk_consumer_group` = `admins`, `warehouse_id` | parses, gitignored; catalog exists; schema created by session 18 |
| P1-6, P1-7 | Open: child build before wave 1-16 (Genie Code with the owner); GitHub setup after merge | - |

## Decisions (owner)
* Consumer group `admins` for dev only; developers choose groups for higher environments (templates keep no defaults).
* Workspace write for the Devin service principal: not granted. The monitor skill forbids workspace writes; gitignored-file fixes go through the owner or Genie Code, then Devin starts a fresh run.
* Hand-off: Devin level 4, `max_repairs` 12, chat-only escalation, P1-6 by Genie Code at wave 1-16 (the monitor skill forbids Devin deploys and setup runs, and an owner answer cannot widen its guardrails), read-only review of the branch changes since `d3fcb9d` after `BUILD_PASSED`.
* Devin's egress IP assumed unchanged since build 0 (allow-list entry kept).

## Housekeeping
* The start-session notebook change was committed (`9ec7598`).
* The 63 untracked build-0 status files under the pre-rename folder `mbp/genie-ontology-sdk/.build-status/` were copied, unchanged, into this project's gitignored `.build-status/`. Removing the old folder waits for the owner's approval.

## Lessons
* Retargeting a genie-build-waves instance after a folder rename needs `--force` on `deploy_instance.py` and `force=true` on the setup job once; the next setup run (after a build-1 run exists) does not.
* `variable-overrides.json` keys the bundle does not declare yet are ignored by `bundle validate --strict`, so overrides can be written ahead of the template change.

## Files modified
* `docs/plans/build-1/REQUESTS.md`, `docs/plans/build-1/INDEX.md`, `docs/plans/waves.json`, plans 18, 23, 23b (new), 25, 27, 28, 29, 30, 43
* `PROJECT_MEMORY.md`, `docs/sessions/2026-11-25_build-1-planning.md` (addenda), this summary, `docs/sessions/INDEX.md`
* `examples/tpch/ontology-genie-agents/agents/ontology_agent.geniespace.json` and `examples/tpch/ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` (deleted)
* `Genie Code Start Session - DO NOT EDIT.ipynb`
* Gitignored, not committed: SDK bundle overrides, both TPC-H overrides, `.local/build-1.json`, `.build-status/` copies; outside the repo: the instance vars file
