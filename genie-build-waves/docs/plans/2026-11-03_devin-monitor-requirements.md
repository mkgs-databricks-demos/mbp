# Requirements: Devin as an external monitor for build-waves runs

Status: **draft 2026-11-03; monitor skill implemented 2026-11-09 (levels 1-3), level 4 added 2026-11-12; first end-to-end test passed at levels 1-3 with no repairs.** Optional add-on. Nothing in the bundle depends on it; the [continuation pass](2026-11-03_continuation-pass.md) handles sessions that run out of steps inside the job, for every user.

## Role

Devin (Cognition) watches a build job from outside the workspace and does what only an outside observer can:

* report each wave's result and the reason for any failure;
* repair runs whose cause is transient or already fixed;
* escalate what needs a person.

It does **not** run sessions, edit project code (except at the optional levels 3-4, through Git only), change the manifest, deploy the bundle, or resume Genie Code conversations. Genie Code job-task conversations can only be continued interactively after the task ends ([Genie Code task for jobs](https://docs.databricks.com/aws/en/jobs/tasks/genie-code/)); there is no API to post into them.

### Levels

| Level | Devin may | Databricks permission on the build job |
|---|---|---|
| 1. Report (start here) | Read run state, task outputs, gate and status files; send a summary | `CAN_VIEW` |
| 2. Repair | Level 1, plus `repair-run` / `run-now --only` for the cases in the decision table | `CAN_MANAGE_RUN` |
| 3. Fix and repair (optional) | Level 2, plus push a fix to the build branch, then repair from `w<w>_sync` | `CAN_MANAGE_RUN`, and Git write access to the build branch |
| 4. Act for the owner (optional) | Level 3 on the owner's standing instruction to complete a build: start its first run, fix files the failed session owns when the cause is quotable, start one fresh run after a refused repair; at most `max_repairs` (default 3) repairs and fresh runs, 2 attempts at the same failure; escalate only on the stop conditions in the monitor skill (guardrail 9) | Same as level 3; no new grants |

Never grant `CAN_MANAGE` or `IS_OWNER`: setup (`jobs/reset`), deploys and permission changes stay with the instance owner.

Levels 3 and 4 rely on the branch sync task (`git` / `hybrid` workflows, `workflow.sync_branch` on, see Branch Sync in `docs/manifest-schema.md`): the integrator commits from the `build_root` Git folder and never pulls, so a pushed fix only reaches the run when the repair starts at `w<w>_sync`, which pulls the branch into the folder first. Rules for a level 3-4 monitor:

* **One writer at a time.** Push only when no build run is active (the build job runs one run at a time; a repair can only start on a finished run). Never push while a run is in progress: the integrator's push would be rejected.
* Push to the build branch only, never `main`, fast-forward only. Keep the fix out of the `owned_paths` of sessions that will re-run, or the pull can conflict with their uncommitted files (the sync then fails and lists them). Level 4 may fix the failed session's own files: that session's uncommitted changes are what failed, and a conflict there shows as `SYNC_FAILED` (report it, do not retry).
* After pushing, repair from `w<w>_sync` with `rerun_dependent_tasks: true`, and check `wave_<w>_sync.json` lists the fix commit.
* The monitor still never edits files in the Databricks workspace (`build_root` stays `CAN_READ`); its changes arrive only through Git.

## Databricks side: identity and authentication

### Service principal

* Create a **dedicated** service principal per instance (or per team), for example `build-waves-monitor`. Do not reuse a deploy principal, a job `run_as` principal, or a personal token.
* Give it the **Workspace access** entitlement (needed for the Jobs and Workspace APIs). No other entitlements.
* Authenticate with **OAuth machine-to-machine** (client ID + OAuth secret): [Authorize service principal access with OAuth](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m/). The CLI and SDKs pick it up from `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` ([unified authentication](https://docs.databricks.com/aws/en/dev-tools/auth/index/)) and exchange it for short-lived tokens.
* Do not use personal access tokens. If Devin later documents an OIDC token issuer for its sessions, prefer workload identity federation (no stored secret) over the OAuth secret.
* Set an expiry on the OAuth secret and record the rotation date with the instance's other secrets.
* **Scope the OAuth secret** to `jobs` and `workspace` only ([Scoped OAuth secrets](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m/), [API scopes](https://docs.databricks.com/api/workspace/scopes)). A secret created without scopes gets `all-apis`. Scopes are fixed when the secret is generated; to change them, generate a new secret.
  * `jobs`: `jobs get`, `list-runs`, `get-run`, `get-run-output` and, at level 2, `repair-run` / `run-now`.
  * `workspace`: `workspace export` of the files under `build_root`.
  * `databricks current-user me` (acceptance check 1) works with any scoped token.
  * Do not add `authentication` (a secret with it can mint tokens with any scope), `sql` or `unity-catalog` (the gate notebook does the UC reads).
  * Levels 1-4 use the same scopes; only the job permission and Git access change.
  * Bundle `validate` with a warehouse `lookup` needs `sql`. Leave it out: the monitor reports that validate error and the owner (or the job's sessions) validate instead.
* **Set the scopes in the CLI profile too.** The Databricks CLI (v1.23) requests `all-apis` by default, so a scoped secret is refused. Give the monitor a profile with `scopes = jobs,workspace` (no secret in the file; the secret stays in the environment). Add `files` only to read the published monitor skill from UC (below).
* Scopes are coarse: `jobs` also covers create, update, delete and cancel, and `workspace` covers import and delete. The object grants below are what keep the monitor read-only (level 1) or limited to runs (level 2); keep both layers.

### Grants

| Object | Grant | Why |
|---|---|---|
| Build job | `CAN_VIEW` (level 1) or `CAN_MANAGE_RUN` (levels 2-3); secret scope `jobs`. Declared in the bundle: bundle variables `monitor_principal` and `monitor_job_level` (the deploy sets the job ACL; clearing the principal revokes it) | `jobs get`, `get-run`, `get-run-output`; repairs |
| `build_root` folder | `CAN_READ`; secret scope `workspace` | `<status_dir>/<run_id>/*.json` (gate, gate result, runtime, session status files), `docs/sessions/` summaries, the manifest. On a Git folder, `CAN_READ` allows `workspace export` |
| The project's dev deploy folders (optional) | Only those folders, never the shared `/Workspace/.bundle` (a grant there covers every bundle deployed under it). Plain-folder `CAN_READ` may not allow `workspace export`; test one export before relying on it | Helps diagnose a failed deploy |
| Setup and smoke jobs | none (optionally `CAN_VIEW`) | Devin never runs setup |
| Unity Catalog data | none | The gate notebook does the UC reads; Devin only reads its results |
| Monitor UC Skill (optional) | `USE CATALOG` on `skills_catalog`, `USE SCHEMA` on `skills_schema`, `READ VOLUME` on `genie_build_monitor` only. Granted by setup when the bundle variable `monitor_principal` is set | Lets the monitor load the skill from UC instead of its repo clone. Never `READ VOLUME` on the schema (it would cover the other skills). Reading it also needs the `files` OAuth scope (`scopes = jobs,workspace,files`; without it: `Invalid scope, required scopes: files`). The file is at `/Skills/<skills_catalog>/<skills_schema>/genie_build_monitor/SKILL.md` (Files API or `databricks fs cat`), not under `/Volumes`. Checked 2026-11-12 |

Repairs and new runs execute as the job's own `run_as` identity, not as the service principal; the principal only needs permission to manage runs. Verify this once with a no-op repair before relying on level 2. A run the monitor starts may still list the job owner as its creator: confirm the caller in the workspace audit log (`system.access.audit`, service `jobs`, action `runNow` / `repairRun`) before relying on the creator field.

Anything shared with the `users` group (dashboards, folders, queries) is readable by the monitor too, and folder names stay visible when something inside a folder is shared. That is the workspace baseline; the read-scope guardrail in the monitor skill limits what it opens.

### Network

* If the workspace has IP access lists or private connectivity, allow the monitor's egress before the acceptance checks (a blocked call fails with `Source IP address ... is blocked by Databricks IP ACL`). Allow the narrowest range (a `/32` when you know the address). A change takes a few minutes to apply; retry after about 5 minutes. The address can change between sessions, so ask the agent's vendor for its egress range.
* The OAuth token endpoint is on the workspace host (`https://<workspace-host>/oidc/v1/token`), so one hostname covers both.

## Devin side

### Organization and repository

* A Devin organization with automations enabled. Levels 1-2: only the repo holding the bundle docs and skills needs to be readable; **write access is not required**.
* Levels 3-4: a Git token for the project repo only. Minimum on a fine-grained token: **Contents: Read and write** (push to the build branch). Add **Pull requests: Read and write** only to post the code review. Keep `main` protected. Prefer the monitor's own Git identity (a machine user or a GitHub App): with a person's token, its commits show that person as the author, and only the commit prefix and trailer (monitor skill guardrail 8) tell them apart.
  * Public repo: Devin sessions can clone it without the GitHub App.
  * Private repo: install the Devin GitHub App with **Only select repositories** and grant it to the Devin organization ([Devin GitHub integration](https://docs.devin.ai/integrations/gh)). The app requests broad read/write permissions; scope it to this repo.

### Environment (blueprint)

* Databricks CLI, pinned to the version the bundle documents (`databricks --version`). Install the Python SDK only if the monitor skill needs it.
* Secrets: `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`. Store them as **personal secrets on a Devin service user you manage** (or your own personal secrets while testing), not as organization secrets, which every session in the Devin organization can read. See [Secret Management in Devin](../../../unity-gateway/devin-mcp/docs/guide.md#secret-management-in-devin) for the scopes and what is still unverified.
* Ignore any Databricks credentials already present in the environment from other teams; the monitor must use its own principal. Have the first step print `databricks current-user me` and stop if the identity is not the monitor principal.

### Network policy

Automation sessions start with a restricted network policy. Add only `<workspace-host>` (plus the Git host if the repo is private). Do not set an unrestricted policy. Set it in the agent's settings: a host limit written only in the prompt is not enforced.

### Automation

| Setting | Value |
|---|---|
| Trigger | Preferred: the build job's notifications (`on_start`, `on_success`, `on_failure`) sent to a Devin incoming-webhook trigger. Fallback: a schedule (for example every 30 minutes) with a Preflight check script that exits without starting a session when the build job has no active or newly finished run. |
| Action | Start a session with the monitor skill and the job ID, or message one long-running session (`auto_create`) so context carries across a multi-day build. |
| Concurrency | 1 run at a time; queue depth small (events for the same run are redundant). |
| Limits | Per-session ACU limit; invocation rate limit. |
| Run as | The automation creator (or the managed service user), so sessions are attributed to the instance owner and receive that identity's personal secrets. Running as organization uses the system user, which has no personal secrets. Verify secret visibility before go-live. |
| Notifications | Email to the instance owner, or a Slack channel if the Devin organization has Slack connected. |
| Tags | A session tag per instance, to track cost. |

Open: Databricks webhook notification destinations send a fixed payload with optional basic auth; confirm the Devin webhook trigger accepts it (or needs a relay) before relying on it.

### Instructions

The tool-agnostic `genie-build-monitor` skill in this bundle (`src/skills/genie-build-monitor/SKILL.md`, written 2026-11-09, level 4 added 2026-11-12), built from `docs/prompts/repair-failed-wave.md` and the README. It covers report, repair, fix and repair (level 3), acting for the owner (level 4) and the code review after the build.

Whoever drives the agent (a person or a Genie Code session): read its latest messages before asking for a report again, and treat its review findings as claims to check against the docs and the code, not as facts. Devin reads it from its clone of the repo; Genie Code users can use the same file. A Devin playbook can point at it instead of copying it.

## What the monitor reads and calls

| Need | Call |
|---|---|
| Find the instance's runs | `jobs list-runs --job-id <id>` |
| Run and task state, repair history | `jobs get-run <run_id> --include-history` |
| Gate and verdict messages | `jobs get-run-output <task_run_id>` for `w<w>_gate` and `build_verdict` |
| Gate details | `workspace export <build_root>/<status_dir>/<run_id>/wave_<w>_gate.json` (and `_gate_result.json`, `_runtime.json`, `_sync.json`) |
| Session details | `workspace export .../<run_id>/<session_id>.json`, `docs/sessions/*-<session_id>-*.md` |
| Repair (level 2) | `jobs repair-run <run_id>` with `rerun_tasks`, `rerun_dependent_tasks: true`, `latest_repair_id`, and the run's original `job_parameters` (`branch`, `build_root`, `manifest_path`) |

## Decision table

Levels 3 and 4: see the decision table in the monitor skill (section 4), which is the source of truth.

| Observation | Level 1 | Level 2 |
|---|---|---|
| Wave passed | Report | Report |
| Genie Code task failed after its retries (`INTERNAL_ERROR: start_agent_run`) | Report | Repair from `w<w>_sessions` |
| Session still incomplete after the continuation pass | Report session, conversation and `progress.next` | Same; do not repair (a person resumes it) |
| Integrator failed, sessions passed | Report | Repair from `w<w>_integrate` |
| Branch sync failed (`branch sync failed` in the verdict) | Report the error and conflicting files from `wave_<w>_sync.json` | Report; repair from `w<w>_sync` only if the cause is gone (for example the folder is back on the build branch). Level 3: fix your own conflicting push, then repair from `w<w>_sync` |
| Code fix needed in a file no re-running session owns | Report the fix | Report. Level 3: push the fix, then repair from `w<w>_sync` |
| Runtime gate failed on soak or probes only | Report | Report; repair from `w<w>_gate` only if the cause was external and is gone |
| Session `blocked`, or gate lists `requests` | Report and escalate | Same |
| Repair refused ("job structure has changed") | Report; the owner decides on a fresh `--only` run | Same |
| Branch missing on the remote | Report; see "Retarget after merge" | Same |
| Anything else | Report and escalate | Same |

Limit level 2 to one automatic repair per wave per run; after that, escalate.

## Acceptance checks

1. From a Devin session: `databricks current-user me` returns the monitor principal.
2. `jobs get <build_job_id>` succeeds; `jobs get` on a job not shared with the principal (or its groups) is denied.
3. Exporting a file under `build_root` (the manifest works before the first run) succeeds; exporting a file in a folder shared with neither the principal nor `users` (for example the owner's own bundle deploy folder) is denied or reports "doesn't exist". Do not test with a listing: folder names are visible when anything inside is shared.
4. A call outside the secret's scopes (for example `databricks catalogs list`) is rejected, which shows the secret is scoped and not `all-apis`.
5. Level 2 only: a repair of a finished smoke run succeeds and runs as the job's `run_as`.
6. Levels 3-4: `git push --dry-run origin <build_branch>` succeeds before the first run. After a push to the build branch, a repair from `w<w>_sync` reports `SYNC_PULLED` with the pushed commit, and the integrator's next push succeeds.
7. A test notification (or one scheduled tick) produces one report and no duplicate sessions.

## Open questions

* Devin egress range for workspaces with IP access lists (one session's address was observed; the range is not published).
* Whether automation sessions run as creator, and child sessions, receive personal secrets (test with a dummy personal secret; report only whether it is set).
* Webhook payload compatibility (see Automation).
